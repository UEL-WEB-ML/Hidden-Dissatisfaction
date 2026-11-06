#!/bin/bash
# Thứ tự quan trọng: các file sau ghi đè bản cũ của file trước.
set -e
cd "$(dirname "$0")"
python3 build_bpmn.py && python3 build_other.py && python3 build_erd.py && python3 build_fix1.py && python3 build_dfd.py && python3 build_state.py
rm -f png/*.png && python3 render.py png drawio/*.drawio | grep -c ok
