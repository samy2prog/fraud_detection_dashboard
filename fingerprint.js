// Script de collecte des empreintes numériques des utilisateurs
// À intégrer sur une page HTML

(async function() {
    // Récupérer les informations du navigateur
    const fingerprint = {
        user_agent: navigator.userAgent,
        ip_address: await fetch('https://api64.ipify.org?format=json')
            .then(response => response.json())
            .then(data => data.ip)
            .catch(() => '0.0.0.0'), // Fallback en cas d'échec
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        language: navigator.language
    };

    // Envoyer les données à l'API
    fetch('http://127.0.0.1:8000/collect_fingerprint/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(fingerprint)
    })
    .then(response => response.json())
    .then(data => console.log('Fingerprint stored:', data))
    .catch(error => console.error('Error storing fingerprint:', error));
})();
