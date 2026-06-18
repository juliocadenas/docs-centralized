#!/usr/bin/env node
// Build script for AI Hub Studio - runs next build from the correct directory
const { execSync } = require('child_process');
const path = require('path');

const studioDir = path.join(__dirname, 'ai-hub-studio');
const nextBin = path.join(studioDir, 'node_modules', 'next', 'dist', 'bin', 'next');

console.log('Studio dir:', studioDir);
console.log('Next bin:', nextBin);
console.log('Building...\n');

try {
    execSync(`node "${nextBin}" build`, {
        cwd: studioDir,
        stdio: 'inherit',
        env: { ...process.env, NODE_PATH: path.join(studioDir, 'node_modules') }
    });
    console.log('\nBuild successful!');
} catch (e) {
    console.error('\nBuild failed:', e.message);
    process.exit(1);
}