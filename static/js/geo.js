async function startLocationReminderWatcher() {
  if (!("geolocation" in navigator)) {
    alert("Geolocation is not supported by this browser.");
    return;
  }

  navigator.geolocation.watchPosition(
    async (pos) => {
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
      const res = await fetch("/api/locations/check-proximity", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        }),
      });
      const data = await res.json();
      if (data.alerts && data.alerts.length > 0) {
        data.alerts.forEach((alertObj) => {
          if ("Notification" in window && Notification.permission === "granted") {
            new Notification(`ConsciousCart: Near ${alertObj.location}`, {
              body: alertObj.message,
              icon: "/static/icons/icon-192.png",
            });
          } else {
            alert(alertObj.message);
          }
        });
      }
    },
    (err) => console.warn("Location permission declined or unavailable:", err.message),
    { enableHighAccuracy: true, maximumAge: 60000, timeout: 15000 }
  );
}