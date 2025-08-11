#!/bin/bash

# Submit Redis AI Challenge entries to DEV.to
# Get your API key from: https://dev.to/settings/extensions

if [ -z "$DEV_TO_API_KEY" ]; then
    echo "❌ Please set DEV_TO_API_KEY environment variable"
    echo "Get your key from: https://dev.to/settings/extensions"
    exit 1
fi

echo "🚀 SUBMITTING REDIS AI CHALLENGE ENTRIES TO DEV.TO"
echo "=================================================="

# Submit Beyond the Cache category
echo "📝 Submitting 'Beyond the Cache' entry..."
response1=$(curl -s -X POST https://dev.to/api/articles \
  -H "Content-Type: application/json" \
  -H "api-key: $DEV_TO_API_KEY" \
  -d @DEV_TO_SUBMISSION_1.json)

if echo "$response1" | grep -q '"url"'; then
    url1=$(echo "$response1" | grep -o '"url":"[^"]*' | cut -d'"' -f4)
    echo "✅ Beyond the Cache submission published: $url1"
else
    echo "❌ Beyond the Cache submission failed:"
    echo "$response1"
fi

echo ""

# Submit Real-Time AI Innovators category  
echo "📝 Submitting 'Real-Time AI Innovators' entry..."
response2=$(curl -s -X POST https://dev.to/api/articles \
  -H "Content-Type: application/json" \
  -H "api-key: $DEV_TO_API_KEY" \
  -d @DEV_TO_SUBMISSION_2.json)

if echo "$response2" | grep -q '"url"'; then
    url2=$(echo "$response2" | grep -o '"url":"[^"]*' | cut -d'"' -f4)
    echo "✅ Real-Time AI Innovators submission published: $url2"
else
    echo "❌ Real-Time AI Innovators submission failed:"
    echo "$response2"
fi

echo ""
echo "🏆 REDIS AI CHALLENGE 2025 SUBMISSIONS COMPLETE!"
echo "Both revolutionary articles are now live on DEV.to"