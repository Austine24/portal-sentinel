import type { ChainConfig } from "./schemas";

interface Eip1193Provider {
  request(args: { method: string; params?: unknown[] | object }): Promise<unknown>;
}

export class WalletError extends Error {}

function provider(): Eip1193Provider {
  const eth = (window as unknown as { ethereum?: Eip1193Provider }).ethereum;
  if (!eth) throw new WalletError("No Ethereum wallet found in this browser. Install MetaMask, then reload this page.");
  return eth;
}

const hexChainId = (config: ChainConfig) => "0x" + config.chain_id.toString(16);

async function ensureChain(eth: Eip1193Provider, config: ChainConfig): Promise<void> {
  try {
    await eth.request({ method: "wallet_switchEthereumChain", params: [{ chainId: hexChainId(config) }] });
  } catch (err) {
    if ((err as { code?: number }).code !== 4902) throw err;   // 4902: the wallet does not know this network yet
    await eth.request({
      method: "wallet_addEthereumChain",
      params: [{
        chainId: hexChainId(config),
        chainName: "Portaldot V3 Testnet",
        nativeCurrency: { name: config.native_symbol, symbol: config.native_symbol, decimals: 18 },
        rpcUrls: [config.rpc_url],
        blockExplorerUrls: [config.explorer_url],
      }],
    });
  }
}

/** Opens the wallet so the USER approves the transaction. Sentinel never sees a key or a seed phrase. */
export async function sendRecordTransaction(config: ChainConfig, data: string): Promise<string> {
  if (!config.registry_address) throw new WalletError("The evidence registry has not been deployed yet.");
  const eth = provider();
  try {
    const accounts = (await eth.request({ method: "eth_requestAccounts" })) as string[];
    if (!accounts[0]) throw new WalletError("No wallet account was shared with this page.");
    await ensureChain(eth, config);
    const hash = await eth.request({
      method: "eth_sendTransaction",
      params: [{ from: accounts[0], to: config.registry_address, data }],
    });
    return String(hash);
  } catch (err) {
    if ((err as { code?: number }).code === 4001) throw new WalletError("You rejected the request in the wallet. Nothing was sent.");
    if (err instanceof WalletError) throw err;
    throw new WalletError(`The wallet reported an error: ${(err as Error).message ?? "unknown error"}`);
  }
}
