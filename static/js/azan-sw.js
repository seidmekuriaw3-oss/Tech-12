var CACHE_NAME = 'azan-sw-v1';
var AUDIO_CACHE = ['azan.mp3', 'fajrazan.mp3'];

self.addEventListener('install', function(e) {
    self.skipWaiting();
});

self.addEventListener('activate', function(e) {
    e.waitUntil(clients.claim());
});

self.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'SCHEDULE_AZAN') {
        var prayers = e.data.prayers;
        var now = new Date();
        var nowMin = now.getHours() * 60 + now.getMinutes();

        prayers.forEach(function(p) {
            var parts = p.time.split(':');
            var pMin = parseInt(parts[0]) * 60 + parseInt(parts[1]);
            var diff = pMin - nowMin;
            if (diff > 0 && diff <= 1440) {
                setTimeout(function() {
                    self.registration.showNotification('Prayer Time — ' + p.name, {
                        body: 'It is time for ' + p.name + ' prayer.',
                        icon: '/static/images/mylogo.png',
                        tag: 'azan-' + p.name,
                        requireInteraction: true,
                        data: { prayer: p.name }
                    });
                    self.clients.matchAll().then(function(list) {
                        list.forEach(function(c) {
                            c.postMessage({ type: 'PLAY_AZAN', prayer: p.name });
                        });
                    });
                }, diff * 60 * 1000);
            }
        });
    }
});

self.addEventListener('notificationclick', function(e) {
    e.notification.close();
    e.waitUntil(clients.openWindow('/islamic'));
});
