import { storeToolHandler } from '../tools/store.js';

const input = JSON.parse(process.argv[2]);

storeToolHandler(input)
  .then(result => console.log(JSON.stringify(result)))
  .catch(err => console.error(err));