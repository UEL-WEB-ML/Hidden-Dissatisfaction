import eslint from '@eslint/js';
import angular from '@angular-eslint/eslint-plugin';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: ['dist/**', '.angular/**', 'node_modules/**'],
  },
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.ts'],
    plugins: { '@angular-eslint': angular },
    rules: {
      // Existing feature stubs intentionally contain unused imports while APIs are filled in.
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-empty-object-type': 'off',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@angular-eslint/directive-class-suffix': 'error',
      '@angular-eslint/component-class-suffix': 'error',
    },
  },
);
