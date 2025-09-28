import { createDbPool } from '../lib/db.ts';
import { storeToolHandler } from '../tools/store.ts';

const input = JSON.parse(process.argv[2]);

async function run() {
  await createDbPool();
  const result = await storeToolHandler(input);
  console.log(JSON.stringify(result));
}

run().catch(err => console.error(err));
