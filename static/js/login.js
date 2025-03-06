// Load the flash message
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => alert.remove());
    }, 5000); // Flash message disappears after 5 seconds
