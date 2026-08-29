import { supabase } from '../lib/supabase';

async function verifyAdminChanges() {
  console.log('🧪 STARTING EMPIRICAL END-TO-END VERIFICATION TEST...');

  const shopSlug = 'yesfancy';
  const testColor1 = '#990000'; // Burgundy Red
  const testAnnouncement1 = '🔥 VERIFICATION TEST ANNOUNCEMENT 12345';

  console.log(`1. Simulating Admin update for ${shopSlug}: Primary Color = ${testColor1}, Announcement = "${testAnnouncement1}"...`);

  // Update Supabase Database
  const { data: shopRecord } = await supabase
    .from('shops')
    .update({ announcement_text: testAnnouncement1 })
    .eq('slug', shopSlug)
    .select()
    .single();

  if (!shopRecord) {
    throw new Error('Failed to fetch shop record from Supabase');
  }

  const { error: themeErr } = await supabase
    .from('shop_themes')
    .upsert({
      shop_id: shopRecord.id,
      primary_color: testColor1
    }, { onConflict: 'shop_id' });

  if (themeErr) {
    throw new Error(`Theme upsert failed: ${themeErr.message}`);
  }

  console.log('✅ Supabase database updated successfully.');

  // Fetch Live Storefront HTML
  console.log(`2. Fetching live storefront HTML from http://localhost:4321/?shop=${shopSlug}...`);
  const res = await fetch(`http://localhost:4321/?shop=${shopSlug}`);
  const html = await res.text();

  const containsColor1 = html.includes('#990000');
  const containsAnnouncement1 = html.includes(testAnnouncement1);

  console.log(`   -> HTML contains primaryColor #990000? ${containsColor1 ? '✅ YES' : '❌ NO'}`);
  console.log(`   -> HTML contains announcement text? ${containsAnnouncement1 ? '✅ YES' : '❌ NO'}`);

  if (!containsColor1 || !containsAnnouncement1) {
    throw new Error('Verification TEST 1 FAILED! Live storefront HTML did not reflect admin changes.');
  }

  console.log('🎉 TEST 1 PASSED: Admin settings change reflected LIVE on storefront!');

  // Now Test 2: Update color to Teal (#00A896)
  const testColor2 = '#00A896';
  const testAnnouncement2 = '✨ Festive Harmony Collection is Live!';

  console.log(`3. Reverting Admin update for ${shopSlug}: Primary Color = ${testColor2}...`);

  await supabase
    .from('shops')
    .update({ announcement_text: testAnnouncement2 })
    .eq('slug', shopSlug);

  await supabase
    .from('shop_themes')
    .upsert({
      shop_id: shopRecord.id,
      primary_color: testColor2
    }, { onConflict: 'shop_id' });

  const res2 = await fetch(`http://localhost:4321/?shop=${shopSlug}`);
  const html2 = await res2.text();

  const containsColor2 = html2.includes('#00A896');
  console.log(`   -> HTML contains primaryColor #00A896? ${containsColor2 ? '✅ YES' : '❌ NO'}`);

  if (!containsColor2) {
    throw new Error('Verification TEST 2 FAILED!');
  }

  console.log('🏆 ALL EMPIRICAL VERIFICATION TESTS PASSED SUCCESSFULLY!');
}

verifyAdminChanges().catch(err => {
  console.error('❌ VERIFICATION TEST ERROR:', err);
  process.exit(1);
});
