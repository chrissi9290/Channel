async function loadTokens() {
  const container = document.getElementById("token-list");
  container.innerHTML = "<p>Lade Tokens...</p>";

  try {
    const res = await fetch("https://api.dexscreener.com/latest/dex/pairs");
    const data = await res.json();
    const pairs = data.pairs.slice(0, 10);

    container.innerHTML = "";

    pairs.forEach((token) => {
      const {
        baseToken,
        priceUsd,
        liquidity,
        chainId,
        url,
      } = token;

      const card = document.createElement("div");
      card.className = "bg-gray-800 p-4 rounded shadow hover:shadow-lg transition";

      card.innerHTML = `
        <h2 class="text-xl font-semibold mb-1">${baseToken.name} (${baseToken.symbol})</h2>
        <p class="text-sm text-gray-400">Chain: <span class="uppercase">${chainId}</span></p>
        <p>Preis: $${parseFloat(priceUsd).toFixed(6)}</p>
        <p>Liquidity: $${parseInt(liquidity.usd).toLocaleString()}</p>
        <a href="${url}" target="_blank" class="inline-block mt-3 text-blue-400 underline">Zur DexScreener-Seite</a>
      `;

      container.appendChild(card);
    });
  } catch (err) {
    console.error(err);
    container.innerHTML = "<p class='text-red-500'>Fehler beim Laden der Daten</p>";
  }
}

loadTokens();
setInterval(loadTokens, 60000);