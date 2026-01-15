// Main Service Worker (Combined PWA + Firebase)
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

const CACHE_NAME = 'guestconnect-v2-firebase'; // Updated version
const STATIC_CACHE_NAME = 'guestconnect-static-v5';
const DYNAMIC_CACHE_NAME = 'guestconnect-dynamic-v5';

// --- FIREBASE CONFIGURATION ---
const firebaseConfig = {
    apiKey: "AIzaSyC_00jdAaoy8YuwhD6vqwc2bK55PZ_eouY",
    authDomain: "guestconnect2.firebaseapp.com",
    projectId: "guestconnect2",
    storageBucket: "guestconnect2.firebasestorage.app",
    messagingSenderId: "1059307478512",
    appId: "1:1059307478512:web:836d6a30116854271bd135",
    measurementId: "G-080L2D262S"
};

// Initialize Firebase
try {
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    // Handle background messages via Firebase
    messaging.onBackgroundMessage((payload) => {
        console.log('[sw.js] Received background message ', payload);
        const notificationTitle = payload.notification.title || 'GuestConnect Notification';
        const notificationOptions = {
            body: payload.notification.body || 'You have a new notification',
            icon: '/static/images/icon-192.png',
            badge: '/static/images/icon-192.png',
            vibrate: [200, 100, 200],
            data: payload.data,
            actions: [
                { action: 'open', title: 'Open App' },
                { action: 'close', title: 'Close' }
            ]
        };
        self.registration.showNotification(notificationTitle, notificationOptions);
    });
} catch (error) {
    console.error('[sw.js] Firebase init error:', error);
}

// Static assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/dashboard/',
    '/static/images/icon-192.png',
    '/static/images/icon-512.png',
    '/static/images/favicon.ico',
    '/manifest.json'
];

// Install event - cache static resources
self.addEventListener('install', event => {
    console.log('[Service Worker] Installing v2...');
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Caching static assets');
                // Cache what we can, don't fail if some resources aren't available
                return Promise.allSettled(
                    STATIC_ASSETS.map(url =>
                        cache.add(url).catch(err => {
                            console.log('[Service Worker] Failed to cache:', url, err);
                        })
                    )
                );
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[Service Worker] Activating v2...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE_NAME &&
                        cacheName !== DYNAMIC_CACHE_NAME &&
                        !cacheName.includes('firebase')) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - network first for API, cache first for static
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension, admin, and API requests
    if (url.protocol === 'chrome-extension:' ||
        url.pathname.startsWith('/admin') ||
        url.pathname.startsWith('/api/')) {
        return;
    }

    // For static assets, use cache first
    if (url.pathname.startsWith('/static/') ||
        url.pathname === '/manifest.json' ||
        url.pathname.endsWith('.png') ||
        url.pathname.endsWith('.ico')) {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetch(request).then(networkResponse => {
                        // Cache for future use
                        if (networkResponse.ok) {
                            const responseClone = networkResponse.clone();
                            caches.open(STATIC_CACHE_NAME).then(cache => {
                                cache.put(request, responseClone);
                            });
                        }
                        return networkResponse;
                    });
                })
        );
        return;
    }

    // For navigation requests (HTML pages), use network first with cache fallback
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Don't cache non-successful responses or login pages
                    if (response.ok && !url.pathname.startsWith('/login')) {
                        const responseClone = response.clone();
                        caches.open(DYNAMIC_CACHE_NAME).then(cache => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // If offline, try to serve from cache
                    return caches.match(request).then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // Return a basic offline page if nothing cached
                        return caches.match('/dashboard/');
                    });
                })
        );
        return;
    }

    // For everything else, try network first
    event.respondWith(
        fetch(request)
            .catch(() => caches.match(request))
    );
});

// Handle push notifications
self.addEventListener('push', event => {
    console.log('[Service Worker] Push received');

    let data = {};
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data = { title: 'Notification', body: event.data.text() };
        }
    }

    const title = data.title || 'GuestConnect';
    const options = {
        body: data.body || 'You have a new notification',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        vibrate: [200, 100, 200],
        data: data.data || {},
        actions: [
            { action: 'open', title: 'Open' },
            { action: 'close', title: 'Close' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    console.log('[Service Worker] Notification clicked:', event.action);

    event.notification.close();

    if (event.action === 'close') {
        return;
    }

    // Open the app
    const urlToOpen = event.notification.data?.url || '/dashboard/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(clientList => {
                // Check if there's already a window open
                for (const client of clientList) {
                    if (client.url.includes('/dashboard') && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', event => {
    console.log('[Service Worker] Sync event:', event.tag);
});
