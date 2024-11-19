// Load content based on current path
async function loadContent(path) {
  // console.log('loadContent');
  let url = (path === '/') ? path : `${path}/`;

  //if url ends by //, remove the last /
  // console.log('url: ', url);
  if (url.endsWith('//')) {
    url = url.slice(0, -1);
  }

  // Check go back arrow has been clicked
  // if (url === '/back') {
  //   console.log('Go back arrow clicked');
  // }

  // console.log('url: ', url);
  // Fetch content from Django and inject into main
  try {
    let request = new Request(url, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'include',
    });
    // console.log('loadContent > request: ', request);

    const response = await fetch(request);

    // console.log('loadContent > response: ', response);
    if (!response.ok) {
      throw new Error(`HTTP error - status: ${response.status}`);
    }
    const data = await response.json();

    // console.log('loadContent > data: ', data);

    if (data.type && data.message && (data.type === 'logout_successful')) {
      // disconnect main room socket
      handleRefresh("logout");
      closeMainRoomSocket();
      // console.log('loadContent > logout_successful');
    }
    else {
      document.querySelector('main').innerHTML = data.html;
    }
    // console.log('loadContent > main updated');
    displayMessageInModal(data.message);
    handleFormSubmission();
  } catch (error) {
    console.error('Error loading content:', error);
    document.querySelector('main').innerHTML = '<h1>Error loading content</h1>';
  }
}


// Handle navigation
function navigate(e, path) {
  e.preventDefault();

  // Push the new state into the browser's history
  window.history.pushState({}, '', path);

  loadContent(path);
}


// Listen for popstate events (Back/Forward buttons)
window.onpopstate = () => {
  if (calcGameSocket) {
    calcGameSocket.close();
    calcGameSocket = null;
  }

  loadContent(window.location.pathname);
};


async function reloadNotificationsIfNeeded() {
  const emptyMessage = document.getElementById('notificationContent');
  if (emptyMessage) {
    if (emptyMessage.innerHTML && (emptyMessage.innerHTML.trim() === 'You have no notifications' ||
      emptyMessage.innerHTML.trim() === 'No tienes notificaciones' ||
      emptyMessage.innerHTML.trim() === 'Vous n\'avez pas de notifications')) {
      const message = { type: 'load_notifications' };
      sendMessagesBySocket(message, mainRoomSocket);
    }
  } else {
    // console.log('emptyMessage not found');
    // console.log('emptyMessage: ', emptyMessage);
  }
}


async function changeLanguage(lang) {
  console.log('changeLanguage > lang: ', lang);
  const path = window.location.pathname;

  // console.log('changeLanguage > current django_language:', getCookie('django_language'));

  try {
    const response = await fetch(`/setLanguage/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'include',
      body: JSON.stringify({ language: lang })
    });

    if (response.ok) {
      data = await response.json();
      // console.log('changeLanguage > new django_language:', getCookie('django_language'));
      await fetchTranslations();
      loadContent(path);
      handleRefresh('language');
      await sleep(350);
      reloadNotificationsIfNeeded();
    } else {
      console.error('Error changing language:', response.statusText);
    }
  } catch (error) {
    console.error('Fetch error:', error);
  }
}


// Update variables for translations
async function fetchTranslations() {
  // console.log('fetchTranslations');
  try {
    // console.log('fetchTranslations > /getTranslations/');
    const response = await fetch('/getTranslations/', {
      headers: {
        'X-Custom-Token': 'mega-super-duper-secret-token'
      }
    });

    // console.log('fetchTranslations > response: ', response);
    if (!response.ok) {
      throw new Error(`HTTP error - status: ${response.status}`);
    }

    const translations = await response.json();

    // console.log('fetchTranslations > translations: ', translations);
    notificationMsg = translations.notificationMsg;
    friendRequestReceived = translations.friendRequestReceived;
    friendRequestAccepted = translations.friendRequestAccepted;
    friendRequestDeclined = translations.friendRequestDeclined;
    gameRequestReceived = translations.gameRequestReceived;
    gameRequestAccepted = translations.gameRequestAccepted;
    gameRequestDeclined = translations.gameRequestDeclined;
    gameRequestCancelled = translations.gameRequestCancelled;
    gameWaitingToPlay = translations.gameWaitingToPlay;
    gamePlayNextTournament = translations.gamePlayNextTournament;
    gameRequestUnconnected = translations.gameRequestUnconnected;
    userBlocked = translations.userBlocked;
    userUnblocked = translations.userUnblocked;
    afterBlockMsg = translations.afterBlockMsg;
    afterUnblockMsg = translations.afterUnblockMsg;
    formSubmissionError = translations.formSubmissionError;
    noFriendsmsg = translations.noFriendsmsg;
    selectFriendmsg = translations.selectFriendmsg;
    profileUpdatedmsg = translations.profileUpdatedmsg;

  } catch (error) {
    console.error('Error fetching translations:', error);
  }
}
