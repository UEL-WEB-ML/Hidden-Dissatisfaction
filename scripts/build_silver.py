#!/usr/bin/env python3
import argparse, os, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def dotenv(path):
    values = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            k, v = line.split('=', 1); values[k.strip()] = v.strip().strip('"\'')
    return values
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--env-file', type=Path, default=Path.home()/'.config/docker-environment/.env'); ap.add_argument('--run-id'); ap.add_argument('--dbt-bin'); a=ap.parse_args()
    if not a.env_file.is_file(): raise SystemExit(f'env file unavailable: {a.env_file}')
    d=dotenv(a.env_file)
    user=d.get('POSTGRES_SUPERUSER') or d.get('POSTGRES_USER')
    password=d.get('POSTGRES_SUPERUSER_PASSWORD') or d.get('POSTGRES_PASSWORD')
    if not user or not password: raise SystemExit('Docker env must define POSTGRES_SUPERUSER and POSTGRES_SUPERUSER_PASSWORD (or legacy POSTGRES_USER/POSTGRES_PASSWORD)')
    env=os.environ.copy(); env.update({'SILVER_DB_HOST':d.get('POSTGRES_HOST','localhost'),'SILVER_DB_PORT':d.get('POSTGRES_PORT','5432'),'SILVER_DB_USER':user,'SILVER_DB_PASSWORD':password,'SILVER_DB_NAME':d.get('POSTGRES_DB','ironman')})
    query="select run_id from bronze.ingestion_runs where status='complete' order by completed_at desc limit 1" if not a.run_id else f"select run_id from bronze.ingestion_runs where run_id='{a.run_id}' and status='complete'"
    r=subprocess.run(['docker','compose','--env-file',str(a.env_file),'exec','-T','postgres','psql','-U',user,'-d',env['SILVER_DB_NAME'],'-At','-c',query],cwd=ROOT.parent/'Docker_Environment',env={**env,'PGPASSWORD':password},text=True,capture_output=True,check=True)
    run=r.stdout.strip().splitlines()[0] if r.stdout.strip() else (_ for _ in ()).throw(SystemExit('no completed Bronze run found'))
    dbt = a.dbt_bin or shutil.which('dbt')
    if not dbt: raise SystemExit('dbt executable not found; install dbt-postgres in a virtualenv and ensure dbt is on PATH (or pass --dbt-bin PATH)')
    subprocess.run([dbt,'build','--project-dir',str(ROOT/'dbt'),'--profiles-dir',str(ROOT/'dbt'), '--vars',f'{{source_run_id: "{run}"}}'],cwd=ROOT,env=env,check=True)
if __name__ == '__main__': main()
