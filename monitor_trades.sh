#!/bin/bash
# Monitor Freqtrade trades in real-time

echo "=========================================="
echo "Freqtrade Trade Monitor"
echo "=========================================="
echo ""
echo "Watching for:"
echo "  ✓ Entry signals (BUY)"
echo "  ✓ Exit signals (SELL)"
echo "  ✓ Order placement"
echo "  ✓ Quantity calculations"
echo "  ✓ Trade closures"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

tail -f /tmp/ft_fixed.log | grep --line-buffered -E "(Entering trade|Exiting trade|Stake calculation|Order calculation|Final quantity|placeorder|orderid|Trade closed|profit)"
