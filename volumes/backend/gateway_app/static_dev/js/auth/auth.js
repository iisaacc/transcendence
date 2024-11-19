// TODO -- It doesnt work I think...
function deleteCookie(name) {
  document.cookie = name + '=; Max-Age=-99999999; path=/;';
}


async function handleRefresh(type) {
//  console.warn('handleRefresh called by:\n', new Error().stack.split('\n')[2].trim());
  // First GET request for the main content
  // console.log('handleRefresh > type:', type);

  if (type != 'language') {
    // console.log('handleRefresh > main content');
    fetch(`/home/?status=success&message=Logged%20in%20successfully&type=main`, {
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'x-requested-with': 'XMLHttpRequest',
      },
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          document.querySelector('main').innerHTML = data.html;
        }
      })
      .catch(error => {
        console.error('Error:', error);
      });
  }


  // Second GET request for the header content
  // console.log('handleRefresh > header');
  fetch(`/home/?status=success&message=Logged%20in%20successfully&type=header`, {
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'x-requested-with': 'XMLHttpRequest',
    },
    credentials: 'include'
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        document.querySelector('header').innerHTML = data.html;
        // get the div with id 'userID' and replace its value with the new user id. Example <input type="hidden" id="userID" value="1">
        if (type == 'logout') {
          g_user_id = 0;
        }
        else {
          g_user_id = data.user_id;
        }
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });

  let chatPresent = false;
  // Remove chat on logout and language change
  if (type == 'logout' || type == 'language' || type == 'profile_update') {
    // console.log('handleRefresh > remove chat');
    // remove chat element
    const chatSection = document.getElementById('chatSection');
    if (chatSection) {
      chatSection.remove();
      if (type != 'logout') {
        chatPresent = true;
      }
    }
    const chatButton = document.getElementById('chatButton');
    if (chatButton) {
      chatButton.remove();
    }
  }

  // Add chat
  if (type == 'login' || type == 'refresh' || type == 'oauth' || type == 'signup' || chatPresent) {
    // console.log('handleRefresh > add chat');
    // GET request for chat section
    fetch(`/home/?status=success&message=Logged%20in%20successfully&type=chat`, {
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'x-requested-with': 'XMLHttpRequest',
      },
      credentials: 'include'
    })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          // console.log('Adding chat section');
          document.querySelector('body').innerHTML += data.html;

          // Initialise the chat modal
          const chatModalElement = document.getElementById('chatModal');
          const chatModal = new bootstrap.Modal(chatModalElement);
          chatModal.hide();
          init_listening();

          if (type == 'profile_update') {
            let lang = getCookie('django_language');
            // console.log('handleRefresh > lang:', lang);
            let message = 'Profile updated';
            if (lang === 'fr')
              message = 'Profil mis à jour';
            else if (lang === 'es')
              message = 'Perfil actualizado';
            displayMessageInModal(message);
          }

        }
      })
      .catch(error => {
        console.error('Error:', error);
      });

  }

  if (type != 'language') {
    window.history.pushState({}, '', '/');
  }

  if (type == 'profile_update' || type == 'login' || type == 'refresh' || type == 'oauth' || type == 'signup' || chatPresent) {
//    console.warn('handleRefresh > updating notifications');
    await fetchTranslations();
    await sleep(350);
    reloadNotificationsIfNeeded();
  }
}


// Function to handle OAuth code once available
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function handleOAuthCode(oauth_callback_url) {
  const oauthCode = getCookie('oauth_code');
  if (oauthCode) {
    // console.log("OAuth code found in cookie:", oauthCode);
    // Delete the OAuth code cookie after retrieving it
    deleteCookie('oauth_code');

    try {
      // Send the code to the server to exchange for an access token
      const response = await fetch(oauth_callback_url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie('csrftoken')
        },
        body: JSON.stringify({ code: oauthCode })
      });

      if (response.ok) {
        // console.log("OAuth authentication successful");
        refreshToken();
        await sleep(500);
        handleRefresh("oauth");
      } else {
        console.error("OAuth authentication failed");
      }
    } catch (error) {
      console.error("Error during OAuth authentication:", error);
    }
  }
}

// When the user clicks the "Login with 42" button
function loginButton42() {
  const configElement = document.getElementById('config42login');
  const CLIENT_ID = configElement.getAttribute('data-client-id');
  const REDIRECT_URI = configElement.getAttribute('data-redirect-uri');
  const oauth_callback_url = configElement.getAttribute('oauth-view-url');
  const authUrl = `https://api.intra.42.fr/oauth/authorize?client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&response_type=code&scope=public`;
  const width = 600;
  const height = 600;
  const left = (window.innerWidth / 2) - (width / 2);
  const top = (window.innerHeight / 2) - (height / 2);
  const authWindow = window.open(authUrl, "42OAuthLogin", `width=${width},height=${height},top=${top},left=${left},menubar=no,toolbar=no,location=no,status=no,scrollbars=no,resizable=no`);

  // Polling for OAuth code every second after the popup is opened
  const intervalId = setInterval(function () {
    // Check for the OAuth code in cookies
    const oauthCode = getCookie('oauth_code');
    if (oauthCode) {
      clearInterval(intervalId); // Stop polling once we get the OAuth code
      authWindow.close(); // Close the popup

      // Handle the OAuth code (send to server, etc.)
      handleOAuthCode(oauth_callback_url);
    }
  }, 1000); // Check every 1 second
};

function enable2FA() {
  fetch('/enable2FA/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    },
  })
    .then(response => response.json())
    .then(data => {
      const twoFaButtonEnable = document.getElementById('2fa-button-enable');
      twoFaButtonEnable.style.display = 'none';
      const qrCodeDiv = document.getElementById('2fa-qr-code');
      qrCodeDiv.style.display = 'flex';
      qrCodeDiv.innerHTML = data.html

      if (data.status === 'success') {
        qrCodeDiv.removeChild(document.getElementById('2fa-enable-error'));
      } else {
        qrCodeDiv.removeChild(document.getElementById('2fa-enable-success'));
      }
    })
    .catch(error => {
      console.error('Error:', error);
      document.getElementById('2fa-qr-code').innerHTML = '<p class="text-danger">Failed to enable 2FA. Please try again later.</p>';
    });
}

function confirm2FA() {
  const otpCode = document.getElementById('otp-code').value;
  if (!otpCode) {
    const error = `<p class="alert alert-danger">${document.getElementById('otp-code').placeholder}</p>`;
    document.getElementById('otp-code').insertAdjacentHTML('beforebegin', error);
    return;
  }

  fetch('/confirm2FA/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ otp_code: otpCode })
  })
    .then(response => response.json())
    .then(data => {

      const qrCodeDiv = document.getElementById('2fa-qr-code');
      if (data.status === 'success') {
        const twoFaButtonDisable = document.getElementById('2fa-button-disable');
        twoFaButtonDisable.style.display = 'block';
        qrCodeDiv.innerHTML = `<p class="text-success p-2 m-0">${data.message}</p>`;
      } else {
        const twoFaButtonDisable = document.getElementById('2fa-button-enable');
        twoFaButtonDisable.style.display = 'block';
        qrCodeDiv.innerHTML = `<p class="text-danger p-2 m-0">${data.message}</p>`;
      }
    })
    .catch(error => {
      console.error('Error:', error);
      document.getElementById('2fa-qr-code').innerHTML = '<p class="text-danger">Failed to confirm 2FA. Please try again later.</p>';
    });
}

function verify2FA() {
  // Get the OTP code entered by the user
  const otpCode = document.getElementById('otp_code').value;

  // Retrieve the user ID from the hidden div
  const userId = document.getElementById('config2FA').getAttribute('user-id-2fa');

  // Make a POST request to the URL with the appended user ID
  fetch(`/verify2FA/${userId}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ otp_code: otpCode })
  })
    .then(response => response.json())
    .then(async data => {
      const messageDiv = document.getElementById('2fa-message');

      if (data.status === 'success') {
        messageDiv.innerHTML = `<p class="text-success">${data.message}</p>`;
        refreshToken();
        await sleep(200);
        g_user_id = await getUserID();
        handleRefresh('login');
        connectMainRoomSocket();
      } else {
        messageDiv.innerHTML = `<p class="text-danger">${data.message}</p>`;
      }
    })
    .catch(error => {
      console.error('Error:', error);
      const messageDiv = document.getElementById('2fa-message');
      messageDiv.innerHTML = '<p class="text-danger">Verification failed. Please try again later.</p>';
    });
}

function disable2FA() {
  fetch('/disable2FA/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    },
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        const twoFaButtonEnable = document.getElementById('2fa-button-enable');
        twoFaButtonEnable.style.display = 'block';
        const twoFaButtonDisable = document.getElementById('2fa-button-disable');
        twoFaButtonDisable.style.display = 'none';

        document.getElementById('2fa-qr-code').innerHTML = `<p class="text-success p-2 m-0">${data.message}</p>`;
      } else if (data.error) {
        document.getElementById('2fa-qr-code').innerHTML = `<p class="text-danger p-2 m-0">${data.message}</p>`;
      }
    })
    .catch(error => {
      console.error('Error:', error);
      document.getElementById('2fa-qr-code').innerHTML = '<p class="text-danger">Failed to disable 2FA. Please try again later.</p>';
    });
}

document.addEventListener("DOMContentLoaded", async () => {
  await refreshToken();
  // Set interval to refresh token every 50 seconds
  setInterval(async () => {
    try {
      const newToken = await refreshToken();
      // console.log("Token refreshed");
    } catch (error) {
      console.error("Failed to refresh token:", error);
      // Handle token refresh failure (e.g., redirect to login)
    }
  }, 20 * 1000); // 20 seconds
});

async function refreshToken() {
  try {
    const response = await fetch('/api/refresh-token/', {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error("Failed to refresh token");
    }

    const data = await response.json();

    // check for the message variable in the response body if its == 'Expired Token refreshed'
    if (data.message === 'Expired Token refreshed') {
      // console.log("Expired Token refreshed");
      await sleep(300);
      handleRefresh("refresh");
    }

    // Assuming the new token is in data.token
    return data.token;
  } catch (error) {
    console.error("Error refreshing token:", error);
    throw error;
  }
}
