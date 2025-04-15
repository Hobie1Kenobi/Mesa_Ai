#!/bin/bash

# Install Three.js and related packages for 3D visualization
npm install --save three@0.152.2 @types/three@0.152.1
npm install --save @react-three/fiber@8.13.0 @react-three/drei@9.80.1 --legacy-peer-deps

echo "Three.js and related packages installed successfully!" 