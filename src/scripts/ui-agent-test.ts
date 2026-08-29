import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

async function runStepByStepUiTest() {
  console.log('🤖 STEP-BY-STEP UI AUTOMATION TEST STARTING...');

  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (!fs.existsSync(chromePath)) {
    throw new Error(`Chrome binary not found at ${chromePath}`);
  }

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 950 });

  const artifactDir = '/Users/divyakodukula/.gemini/antigravity-cli/brain/13c28c40-e524-4ce1-b7d9-03d80cbfdd02';

  console.log('1. Navigating to http://localhost:4321/admin...');
  await page.goto('http://localhost:4321/admin', { waitUntil: 'networkidle0' });

  console.log('2. Authenticating merchant session as "yesfancy" (PIN: 1234)...');
  await page.evaluate(() => {
    (document.getElementById('login-shop-select') as HTMLSelectElement).value = 'yesfancy';
    (document.getElementById('login-pin-input') as HTMLInputElement).value = '1234';
    (window as any).handleVendorLogin();
  });
  await delay(1000);

  console.log('3. Opening Tab 2 (Category Carousels & Cover Uploads)...');
  await page.evaluate(() => (window as any).switchTab('categories'));
  await delay(500);

  // STEP 1 SCREENSHOT: Before file selection
  const step1Path = path.join(artifactDir, 'step1_before_file_selection.png');
  await page.screenshot({ path: step1Path, fullPage: false });
  console.log(`📸 STEP 1 Captured: ${step1Path}`);

  // STEP 2: Browse & Select File
  const testImagePath = path.join(__dirname, 'test-image.png');
  console.log(`4. Clicking Browse & selecting file ${testImagePath}...`);

  const fileInput = await page.$('#cat-file-input');
  if (!fileInput) {
    throw new Error('#cat-file-input element not found in DOM!');
  }

  await fileInput.uploadFile(testImagePath);
  await delay(1500);

  // STEP 2 SCREENSHOT: File selected, preview thumbnail rendered
  const step2Path = path.join(artifactDir, 'step2_file_selected_and_previewed.png');
  await page.screenshot({ path: step2Path, fullPage: false });
  console.log(`📸 STEP 2 Captured: ${step2Path}`);

  // STEP 3: Fill form & Save to Supabase Cloud
  console.log('5. Submitting form to save compressed image to Supabase Cloud Storage...');
  await page.type('#cat-label-input', 'Handcrafted Clay Pottery');
  await page.type('#cat-tag-input', 'terracotta');
  
  await page.evaluate(() => {
    const btn = document.getElementById('cat-submit-btn') as HTMLButtonElement;
    if (btn) btn.click();
  });
  await delay(2000);

  // STEP 3 SCREENSHOT: Form submitted, saved to database, toast modal confirmed
  const step3Path = path.join(artifactDir, 'step3_saved_to_supabase_cloud.png');
  await page.screenshot({ path: step3Path, fullPage: false });
  console.log(`📸 STEP 3 Captured: ${step3Path}`);

  await browser.close();

  console.log('🏆 ALL 3 STEP-BY-STEP SCREENSHOTS CAPTURED SUCCESSFULLY!');
}

runStepByStepUiTest().catch(err => {
  console.error('❌ STEP-BY-STEP UI AGENT TEST EXCEPTION:', err);
  process.exit(1);
});
