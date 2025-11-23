// eslint.config.js
import js from '@eslint/js';

export default [
    js.configs.recommended,
    {
        languageOptions: {
            ecmaVersion: 2021,
            sourceType: 'module',
            globals: {
                // Браузерные глобальные переменные
                window: 'readonly',
                document: 'readonly',
                console: 'readonly',
                localStorage: 'readonly',
                WebSocket: 'readonly',
                URL: 'readonly',
                fetch: 'readonly',
                setTimeout: 'readonly',
                clearTimeout: 'readonly',
                setInterval: 'readonly',
                clearInterval: 'readonly',
                AbortController: 'readonly',
                FormData: 'readonly', //  встроенный браузерный API
            },
        },
        rules: {
            'no-unused-vars': 'warn',
            'no-undef': 'off', // Отключено — т.к. браузерные API не видны
            'no-console': 'off',
            semi: ['error', 'always'],
            quotes: ['error', 'single'],
            eqeqeq: 'error',
            'no-var': 'error',
            'prefer-const': 'error',
            'no-duplicate-imports': 'error',
            'prefer-template': 'error',
            'arrow-spacing': 'error',
            'no-trailing-spaces': 'error',
            'eol-last': ['error', 'always'],
            indent: ['error', 4],
            'object-curly-spacing': ['error', 'always'],
            'array-bracket-spacing': ['error', 'never'],
        },
    },
];
