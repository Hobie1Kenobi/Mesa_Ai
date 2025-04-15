import '../styles/globals.css';
import { WagmiConfig, createClient, configureChains } from 'wagmi';
import { baseGoerli, base } from 'wagmi/chains';
import { publicProvider } from 'wagmi/providers/public';
import { CoinbaseWalletConnector } from 'wagmi/connectors/coinbaseWallet';
import { MetaMaskConnector } from 'wagmi/connectors/metaMask';
import { InjectedConnector } from 'wagmi/connectors/injected';
import Head from 'next/head';

// Configure chains & providers
const { chains, provider } = configureChains(
  [base, baseGoerli],
  [publicProvider()]
);

// Set up client
const client = createClient({
  autoConnect: true,
  connectors: [
    new CoinbaseWalletConnector({
      chains,
      options: {
        appName: 'MESA Rights Vault',
      },
    }),
    new MetaMaskConnector({
      chains,
    }),
    new InjectedConnector({
      chains,
      options: {
        name: 'Injected',
        shimDisconnect: true,
      },
    }),
  ],
  provider,
});

function MyApp({ Component, pageProps }) {
  return (
    <WagmiConfig client={client}>
      <Head>
        <title>MESA Rights Vault | Privacy-First Music Rights Management</title>
        <meta name="description" content="A decentralized platform for musicians to register, verify, and transfer music rights with privacy and control." />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        <meta property="og:title" content="MESA Rights Vault | Privacy-First Music Rights Management" />
        <meta property="og:description" content="A decentralized platform for musicians to register, verify, and transfer music rights with privacy and control." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://mesawallet.io/rights-vault" />
        <meta property="og:image" content="https://mesawallet.io/og-image.jpg" />
        <meta name="twitter:card" content="summary_large_image" />
      </Head>
      <Component {...pageProps} />
    </WagmiConfig>
  );
}

export default MyApp; 