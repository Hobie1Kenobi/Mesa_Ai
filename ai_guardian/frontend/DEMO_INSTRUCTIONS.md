# MESA AI Guardian Demo Instructions

This guide will walk you through demonstrating the MESA AI Guardian system, including CSV import functionality, publisher profiles, and 3D visualizations.

## Prerequisites

Make sure you have the following installed:
- Node.js (v14+)
- npm

## Setup Instructions

1. Install dependencies:
   ```bash
   cd MESA_Base_Hackathon/ai_guardian/frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000`

## Demo Walkthrough

### 1. Publisher Dashboard Overview

Start with the Publisher Dashboard, which shows:
- A professional publisher profile with blockchain verification information
- Stats on registered, pending, and failed tracks
- A catalog table of all music tracks with their statuses

### 2. CSV Import Demonstration

1. Click the "Import Catalog" button in the top-right corner
2. In the import modal, either:
   - Drag and drop the `MESA_DEMO_CATALOG.csv` file (from the parent directory)
   - Click to browse and select the file

3. Observe the file preview showing the first rows of the CSV
4. Click "Import Catalog" to process the file
5. Watch the progress bar as the system simulates processing the data
6. Once complete, notice:
   - The newly imported items in the catalog table
   - The updated stats cards with the increased numbers
   - The success notification confirming the import

### 3. 3D Visualization Experience

1. Click the "Analytics" tab in the dashboard
2. Observe the 3D floating, spinning tiles containing your catalog data
3. Interact with the visualization:
   - Drag to rotate the entire scene
   - Hover over tiles to highlight them
   - Click on a tile to enlarge it
   - Scroll to zoom in and out

4. Notice how each tile displays:
   - Track title
   - Artist name
   - Rights ID (for registered tracks)
   - Status (color-coded: blue for registered, yellow for pending, red for failed)

### 4. Publisher Profile Review

Examine the publisher profile card, which displays:
- Verification status and badges
- Catalog statistics and registration rate
- Usage insights with play counts
- Blockchain security information with contract addresses

## Key Features to Highlight

- **Data Completeness**: All imported tracks maintain their metadata through the system
- **Visualization Fluidity**: The 3D visualization is smooth and interactive
- **Blockchain Integration**: Simulated on-chain registration with transaction hashes
- **Modern UI**: Clean, professional design appropriate for music industry professionals
- **Responsive Design**: The interface adapts well to different screen sizes

## Troubleshooting

- If you encounter type errors in the console, these are expected as we're using TypeScript without all the necessary types defined during development
- If the 3D visualization doesn't appear, check that your browser supports WebGL
- If the import seems to hang, try refreshing the page and importing again

## Next Steps After Demo

Discuss how this prototype would be extended to include:
1. Real blockchain interactions with MetaMask
2. Advanced rights management features
3. Integration with music platforms for live usage data
4. Enhanced analytics with historical trend data 