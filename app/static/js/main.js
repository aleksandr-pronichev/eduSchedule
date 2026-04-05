document.addEventListener('DOMContentLoaded', function() {
    var alertBoxes = document.querySelectorAll('.alert-dismissible');
    alertBoxes.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
});
