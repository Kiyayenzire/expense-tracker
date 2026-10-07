(() => {
  const script = document.currentScript;
  if (!script) return;

  const idleTimeoutMs = Number(script.dataset.idleTimeoutSeconds) * 1000;
  const activityUrl = script.dataset.activityUrl;
  const loginUrl = new URL(script.dataset.loginUrl, window.location.origin);
  if (!idleTimeoutMs || !activityUrl || window.location.pathname === loginUrl.pathname) return;

  let lastActivityAt = Date.now();
  let lastHeartbeatActivityAt = lastActivityAt;
  let lastHeartbeatAt = lastActivityAt;
  let heartbeatPending = false;
  let idleTimer;

  const redirectToLogin = () => {
    const next = `${window.location.pathname}${window.location.search}`;
    loginUrl.searchParams.set('next', next);
    window.location.replace(loginUrl.toString());
  };

  const redirectIfIdle = () => {
    if (Date.now() - lastActivityAt < idleTimeoutMs) return false;
    redirectToLogin();
    return true;
  };

  const scheduleIdleCheck = () => {
    window.clearTimeout(idleTimer);
    idleTimer = window.setTimeout(
      redirectIfIdle,
      Math.max(0, idleTimeoutMs - (Date.now() - lastActivityAt)),
    );
  };

  const refreshAdminSession = () => {
    if (heartbeatPending) return;
    heartbeatPending = true;
    lastHeartbeatAt = Date.now();
    fetch(activityUrl, { credentials: 'same-origin', cache: 'no-store' })
      .then((response) => {
        if (response.redirected) {
          redirectToLogin();
          return;
        }
        if (!response.ok) throw new Error(`Admin activity check failed: ${response.status}`);
        lastHeartbeatActivityAt = lastActivityAt;
      })
      .catch((error) => console.error(error))
      .finally(() => {
        heartbeatPending = false;
      });
  };

  const markActivity = () => {
    lastActivityAt = Date.now();
    scheduleIdleCheck();
    if (Date.now() - lastHeartbeatAt >= 60_000) refreshAdminSession();
  };

  ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'].forEach((eventName) => {
    document.addEventListener(eventName, markActivity, { passive: true });
  });

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) redirectIfIdle();
  });

  scheduleIdleCheck();
  window.setInterval(() => {
    if (redirectIfIdle() || lastActivityAt === lastHeartbeatActivityAt) return;
    refreshAdminSession();
  }, 60_000);
})();
