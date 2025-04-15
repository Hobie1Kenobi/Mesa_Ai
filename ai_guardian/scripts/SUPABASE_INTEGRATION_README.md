# MESA Supabase to Blockchain Integration

This integration connects a Supabase database to the Ethereum Attestation Service (EAS) on Base Sepolia, allowing music rights data to be automatically attested on the blockchain.

## Features

- Register music rights metadata schemas on EAS
- Sync music rights data from Supabase to blockchain attestations
- Track attestation status in Supabase
- Automatic retry and error handling
- Detailed logging and state management

## Prerequisites

- Node.js (v14+)
- Supabase project with necessary tables
- Base Sepolia ETH in your wallet

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

Copy the sample environment file and update with your credentials:

```bash
cp .env.supabase .env
```

Edit the `.env` file with:
- Your Supabase URL and service key
- Your Ethereum wallet private key
- Base Sepolia RPC URL
- (Leave ENHANCED_SCHEMA_UID blank for now)

### 3. Set Up Supabase Database

In your Supabase project, execute the SQL in `supabase_setup.sql` to create the necessary tables.

Alternatively, you can create the tables through the Supabase UI:
1. Go to the SQL Editor in your Supabase project
2. Copy and paste the contents of `supabase_setup.sql`
3. Run the SQL script

### 4. Register Enhanced Schema

```bash
npm run register-schema
```

This will:
1. Register the enhanced schema on EAS
2. Save the schema UID to `schema_config.json`
3. Output the schema UID to add to your `.env` file

### 5. Test the Integration

```bash
npm run test
```

This will:
1. Connect to your Supabase database
2. Find pending attestations
3. Process a single attestation for testing
4. Output the attestation UID and transaction hash

## Running in Production

### Continuous Sync Mode

```bash
npm start
```

This will:
1. Process all pending attestations in batches
2. Continue running with a 15-minute interval check for new records
3. Track sync state and handle errors

### Systemd Service (Linux)

To run the sync as a service:

1. Create a systemd service file:

```
[Unit]
Description=MESA Supabase to Blockchain Sync
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/mesa-scripts
ExecStart=/usr/bin/node supabase_to_blockchain_sync.js
Restart=on-failure
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:

```bash
sudo systemctl enable mesa-sync.service
sudo systemctl start mesa-sync.service
```

3. Check service status:

```bash
sudo systemctl status mesa-sync.service
```

## Schema Structure

Our enhanced schema includes the following fields:

| Field | Type | Description |
|-------|------|-------------|
| track_title | string | Title of the music track |
| artist_name | string | Name of the artist |
| publisher | string | Publishing company |
| rights_type | string | Type of rights (songwriting, master, both) |
| jurisdiction | string | Legal jurisdiction |
| rightsholder_name | string | Name of rights holder |
| rightsholder_email | string | Email contact |
| rightsholder_role | string | Type of contribution (role) |
| rightsholder_ipi | string | International Performer Identifier |
| split_percentage | string | Percentage ownership |
| rightsholder_address | string | Physical address |
| rightsholder_phone | string | Phone contact |
| rightsholder_id | string | ID number |
| iswc_code | string | International Standard Work Code |
| isrc_code | string | International Standard Recording Code |
| designated_administrator | string | Who manages the rights |
| wallet_address | address | Blockchain address of rights holder |
| mesa_verified | string | Verification status from MESA |

## View Attestations

Attestations can be viewed on the Base Sepolia EAS Explorer:

```
https://base-sepolia.easscan.org/attestation/view/[ATTESTATION_UID]
```

## Troubleshooting

### Common Issues

- **Supabase Connection Error**: Check your SUPABASE_URL and SUPABASE_SERVICE_KEY
- **Schema Registration Failed**: Ensure you have Base Sepolia ETH in your wallet
- **Transaction Failed**: Check the Base Sepolia network status and your wallet balance
- **Invalid Address**: Ensure wallet addresses are valid Ethereum addresses

### Logs

Check the console output and `sync_state.json` for details on sync status and errors. 