
// Add or remove badge for online friends on my_friends page and chat modal
function updateOnlineFriends(data) {
  //console.log('updateOnlineFriends > data:', data);
  const userIdToUpdate = data.user_id;

  // for my_friends page
  const myfriendsContainer = document.querySelector('.myfriends-container');
  // console.log('myfriendsContainer:', myfriendsContainer);
  if (myfriendsContainer) {

    const friendDiv = myfriendsContainer.querySelector(`div[data-userid="${userIdToUpdate}"]`);
    // If friend is not blocked
    if (friendDiv && !friendDiv.classList.contains('blocked')) {
      const friendOnlineBadge = myfriendsContainer.querySelector(`span[data-online="${userIdToUpdate}"]`);
      // console.log('friendElement:', friendElement);
      if (friendOnlineBadge) {
        if (data.type === 'user_connected') {
          friendOnlineBadge.style.display = 'block';
        }
        else if (data.type === 'user_left') {
          friendOnlineBadge.style.display = 'none';
        }
      }
    }
  }

  // for chat modal
  const contactList = document.querySelector('#contactList');
  // console.log('contactList:', contactList);
  if (contactList) {
    const friendListItem = contactList.querySelector(`li[data-contact-id="${userIdToUpdate}"]`);
    // If friend is not blocked
    if (friendListItem && !friendListItem.classList.contains('blocked-contact')) {
      const friendOnlineBadge = contactList.querySelector(`span[data-online="${userIdToUpdate}"]`);
      // console.log('friendOnlineBadge:', friendOnlineBadge);
      if (friendOnlineBadge) {
        if (data.type === 'user_connected') {
          friendOnlineBadge.style.display = 'block';
        }
        else if (data.type === 'user_left') {
          friendOnlineBadge.style.display = 'none';
        }
      }
    }
  }

}

// function addOnlineStatusBadge(data) {
//   console.log('addOnlineStatusBadge > data:', data);
//   const onlineFriends = data.connected_friends_ids;

//   // for chat modal
//   const contactList = document.querySelector('#contactList');
//   // console.log('contactList:', contactList);
//   if (contactList) {
//     onlineFriends.forEach((userId) => {
//       const friendElement = contactList.querySelector(`span[data-online="${userId}"]`);
//       // console.log('friendElement:', friendElement);
//       if (friendElement) {
//         friendElement.style.display = 'block';
//       }
//     });
//   }

// }