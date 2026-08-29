import fs from 'fs';
import path from 'path';
import { ShopConfigSchema } from '../schemas/shop.schema';

function validateShop(filePath: string) {
  console.log(`🔍 Validating shop config: ${filePath}`);
  const absolutePath = path.resolve(filePath);
  
  if (!fs.existsSync(absolutePath)) {
    console.error(`❌ File not found: ${absolutePath}`);
    process.exit(1);
  }

  const rawContent = fs.readFileSync(absolutePath, 'utf-8');
  const jsonContent = JSON.parse(rawContent);

  const result = ShopConfigSchema.safeParse(jsonContent);

  if (result.success) {
    console.log(`✅ VALID CONFIGURATION for shop: "${result.data.shop.name}" (${result.data.shop.slug})`);
    console.log(`   - Category: ${result.data.shop.category}`);
    console.log(`   - Template: ${result.data.shop.template}`);
    console.log(`   - Products Count: ${result.data.shop.products.length}`);
  } else {
    console.error(`❌ INVALID CONFIGURATION in ${filePath}:`);
    console.error(JSON.stringify(result.error.format(), null, 2));
    process.exit(1);
  }
}

const targetFile = process.argv[2] || './src/shops/yesfancy.json';
validateShop(targetFile);
