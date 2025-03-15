(async function() {
    try {
        console.log("📡 Détection de l'empreinte numérique...");

        // Récupérer l'adresse IP publique (IPv4/IPv6)
        let ip_address = '0.0.0.0'; // Valeur par défaut
        try {
            const ipResponse = await fetch('https://api64.ipify.org?format=json');
            const ipData = await ipResponse.json();
            ip_address = ipData.ip;
        } catch (error) {
            console.warn("⚠️ Impossible de récupérer l'adresse IP :", error);
        }

        // Récupérer les informations du navigateur
        const fingerprint = {
            user_agent: navigator.userAgent,
            ip_address: ip_address,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen_resolution: `${window.screen.width}x${window.screen.height}`,
            language: navigator.language
        };

        console.log("📌 Empreinte générée :", fingerprint);

        // Envoyer les données à l'API FastAPI sur Render
        const apiUrl = "https://TON_API_RENDER.onrender.com/collect_fingerprint/";  // ⚠️ Remplace par ton URL réelle !

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(fingerprint)
        });

        if (!response.ok) {
            throw new Error(`Erreur API : ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log("✅ Empreinte stockée avec succès :", data);

    } catch (error) {
        console.error("❌ Erreur lors de la collecte de l'empreinte :", error);
    }
})();
