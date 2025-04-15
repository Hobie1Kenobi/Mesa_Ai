# 3D Visualization Component for MESA AI Guardian

This document explains how to set up and use the floating 3D visualization component that displays music rights data in an interactive, visually appealing way.

## Installation

1. First, install the required dependencies:
   ```bash
   npm install --save three@0.152.2 @types/three@0.152.1
   npm install --save @react-three/fiber@8.13.0 @react-three/drei@9.80.1 --legacy-peer-deps
   ```

   Or simply run:
   ```bash
   npm install
   ```
   since the dependencies have been added to package.json already.

2. The component is already integrated in the Publisher Dashboard. To see it in action, start the development server:
   ```bash
   npm run dev
   ```

3. Navigate to the Publisher Dashboard and check the Analytics tab.

## How It Works

The visualization creates a 3D space with floating, transparent tiles that display data about music rights. Each tile contains:

- Title of the music
- Artist name
- Rights ID (when available)
- Status (registered, pending, or failed)

Tiles are color-coded by status:
- Blue: Registered
- Yellow: Pending
- Red: Failed

## Customization Options

You can customize the visualization by modifying the `FloatingBubbleChart` component:

- Change tile appearance in the `FloatingTile` component
- Adjust animations in the `useFrame` hook
- Modify the layout pattern in the `transformedData` calculation
- Change colors in the `getColor` function

## Using in Other Components

To use this visualization in other parts of the application:

```tsx
import FloatingBubbleChart from '../components/FloatingBubbleChart';

// In your component:
<FloatingBubbleChart 
  data={yourDataArray} 
  height="400px" // Optional, defaults to 600px
/>
```

The `data` prop should be an array of objects containing at least:
- `id`: Unique identifier
- `title`: Title text to display
- `status`: 'registered', 'pending', or 'failed'

Other useful properties:
- `artist`: Artist name
- `rightsId`: Blockchain rights ID
- `isrc`: International Standard Recording Code
- `iswc`: International Standard Musical Work Code

## Interactive Features

- **Hover**: Highlights a tile
- **Click**: Enlarges a tile
- **Drag**: Rotates the entire view
- **Scroll**: Zooms in and out

## Troubleshooting

If you encounter any issues:

1. Check that all dependencies are correctly installed
2. Ensure your Three.js version is compatible with react-three-fiber (v8.13.0 works with Three.js v0.152.x)
3. If you see errors about JSX elements or type definitions, try restarting the development server

For any further questions, refer to the react-three-fiber documentation: https://docs.pmnd.rs/react-three-fiber 