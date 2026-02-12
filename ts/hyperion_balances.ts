import * as dotenv from "dotenv";
import { Aptos, AptosConfig, Network } from "@aptos-labs/ts-sdk";

dotenv.config();

const config = new AptosConfig({ network: Network.MAINNET });
// Aptos is the main entrypoint for all functions
const client = new Aptos(config);

const args = process.argv.slice(2);
const HYPERION_DEX_ADDRESS = args[0];
const decimals = Number(args[1]);
const block = Number(args[2]);
const objectIds: Array<any> = JSON.parse(args[3]);
const susdeUsdcPool =
  "0x6dbccb32fb5640127ac20d307c3780eb738f12cefc0ebd8c3ba5e1593f2e6ed3";
const susdeObjectId =
  "0xb30a694a344edee467d9f82330bbe7c3b89f440a1ecd2da1f3bca266560fce69";

async function getStrategy() {
  // iterate over all users and get their susde balance
  const user_balances: Record<string, number> = {};
  let ownerObjectIds: Record<string, string[]> = {};

  for (const v of objectIds) {
    const objectId = v.object_id;
    const ownerAddress = v.owner_address;

    if (!ownerObjectIds[ownerAddress]) {
      ownerObjectIds[ownerAddress] = [];
    }

    if (!ownerObjectIds[ownerAddress].includes(objectId)) {
      ownerObjectIds[ownerAddress].push(objectId);
    }
  }

  for (const ownerAddress in ownerObjectIds) {
    const objectIds = ownerObjectIds[ownerAddress];
    let totalAmount = 0;

    for (const objectId of objectIds) {
      try {
        let [susdeAmount, usdcAmount] = await client.view<any[]>({
          payload: {
            function: `${HYPERION_DEX_ADDRESS}::router_v3::get_amount_by_liquidity`,
            functionArguments: [objectId],
          },
          options: { ledgerVersion: block },
        });

        let [swapUsdcAmount] = await client.view<any[]>({
          payload: {
            function: `${HYPERION_DEX_ADDRESS}::pool_v3::get_amount_out`,
            functionArguments: [susdeUsdcPool, susdeObjectId, susdeAmount],
          },
          options: { ledgerVersion: block },
        });

        totalAmount = totalAmount + usdcAmount + swapUsdcAmount;
      } catch (e) {
        console.error(e);
      }
    }

    user_balances[ownerAddress] = scaleDownByDecimals(totalAmount, decimals);
  }

  console.log(JSON.stringify(user_balances));
}

function scaleDownByDecimals(value: number, decimals: number) {
  return value / 10 ** decimals;
}

const strategy = getStrategy().catch(console.error);
