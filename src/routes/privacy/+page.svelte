<script lang="ts">
  import Card from '$lib/components/ui/Card.svelte';
</script>

<div class="max-w-4xl mx-auto space-y-6">
  <h1 class="text-2xl font-bold">Privacy Policy</h1>

  <Card>
    <div class="prose prose-invert prose-sm max-w-none space-y-4 text-white/70">
      <p><strong class="text-white">1. Information We Collect</strong><br>We collect account information (name, email), content uploaded for analysis (video, audio, text), and usage data (page views, feature usage, token consumption).</p>
      <p><strong class="text-white">2. How We Use Information</strong><br>Uploaded content is used solely for analysis and is not shared with third parties. We use usage data to improve our service and models. Account data is used for authentication and communication.</p>
      <p><strong class="text-white">3. Data Storage</strong><br>Analysis results are stored securely on our servers. Uploaded media files are processed and deleted within 72 hours. Analysis scores and recommendations are retained for 90 days to provide history access.</p>
      <p><strong class="text-white">4. Data Sharing</strong><br>We do not sell your personal data. We may share anonymized, aggregated data for research purposes. We comply with lawful requests from authorities.</p>
      <p><strong class="text-white">5. Security</strong><br>We implement industry-standard encryption for data in transit (TLS) and at rest (AES-256). Authentication uses HTTP-only cookies to prevent XSS attacks.</p>
      <p><strong class="text-white">6. Your Rights</strong><br>You may export or delete your data at any time through account settings. You may request deletion by contacting support. Data is removed within 30 days of request.</p>
      <p><strong class="text-white">7. Cookies</strong><br>We use essential cookies for authentication (neuralpulse_token). No third-party tracking cookies are used. Session data is stored in server-side sessions.</p>
      <p><strong class="text-white">8. Contact</strong><br>For privacy inquiries, contact privacy@neuralpulse.ai. Data controller: NeuralPulse AI, Inc.</p>
    </div>
  </Card>
</div>
