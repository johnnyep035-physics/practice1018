/*
 * main.js
 * 訂單管理系統通用前端腳本
 */

document.addEventListener('DOMContentLoaded', () => {
    // 自動於 5 秒後淡出一般提示通知 (保留警告與錯誤提示)
    const alerts = document.querySelectorAll('.alert-success, .alert-info');
    alerts.forEach(alertEl => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
});
