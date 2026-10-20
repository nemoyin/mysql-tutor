import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'../tests/e2e',timeout:45000,use:{baseURL:'http://127.0.0.1:18765',headless:true,channel:'chrome'},workers:1,reporter:'list'});
