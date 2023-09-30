$(function () {
  getChatList();
});

const authUserName = localStorage.getItem('auth_username');
const authUserId = localStorage.getItem('auth_id');
let currentChat
let activeChatUserName
let divScrollHeight

function getChatList (query='') {
  $.ajax({
    url: `/api/v1/chat/chatlist/?search=${query}`,
    type: 'GET',
    success: function (data) {
      handlerChatList(data)
      // чтобы не множить количество обработчиков мы удаляем старый и привязываем новый
      $('.chats').off('click').on('click', getMessages)
      $('#search-btn').off('click').one('click', handlerSearch)
      handlerActiveChat()
      getActiveChatMessages()

    },
    error: function (data) {
      console.log('error', data);
    }
  })
}

function getMessages(event, page) {
  let chatId
  let pageNumber
  // проверяем была ли функция вызвана с аргументом или без
  if (typeof page === 'undefined') {
    pageNumber = 1
    const chat = $(this)
    chatId = chat.attr('id')
    currentChat = chatId
  } else {
    pageNumber = page
    chatId = currentChat
  }
  $.ajax({
    url: `/api/v1/chat/messages/${chatId}/?page=${pageNumber}`,
    type: 'GET',
    success: function(data) {
      handlerUserInfo()
      handlerListMessages(data.results)
      // если след стр нет то это значит что мы загрузили первую и поэтому мы попадаем в конец дива то есть в начало переписки
      if (data.previous == null) {
        $('.chat-messages')[0].scrollTop = $('.chat-messages')[0].scrollHeight;
      } else {
        // если загружаются все остальные страницы то мы остаемся на том же месте откуда подгрузилась новая переписка
        // из новый общей высоты дива мы вычитаем старую высоты которую храним в divScrollHeight
        $('.chat-messages')[0].scrollTop = $('.chat-messages')[0].scrollHeight - divScrollHeight;
      }
      // если есть еще страницы для загрузки то мы снова вешаем обработчик и вызываем функцию пагинации
      if (data.next != null) {
        $('.chat-messages').on('scroll', function() {
          handlerEndlessPagination(data.next)
        });
      }
    },
    error: function(data) {
      console.log('error', data)
    }
    })
}

function getActiveChatMessages() {
  const url = new URL(window.location.href)
  const params = url.searchParams
  chatId = params.get('chat_id')
  if(chatId) {
    document.getElementById(chatId).click();
    window.history.replaceState({}, '', url.origin)
  }
}

function formatDate(data_date) {
  const date = new Date(data_date);

  const options = {
    hour: 'numeric',
    minute: 'numeric',
    hour12: true
  };

  return date.toLocaleString('en-US', options);
}

function handlerActiveChat() {
  const listItems = document.querySelectorAll('.chat-list li');
  let selectedItem;

  listItems.forEach((item) => {
  item.addEventListener('click', (event) => {
    if (selectedItem) {
      selectedItem.classList.remove('active');
      selectedItem.classList.remove('disabled');
    };

    selectedItem = event.currentTarget;
    selectedItem.classList.add('active');
    selectedItem.classList.add('disabled');
    activeChatUserName = selectedItem.querySelector('.name').textContent;
    document.querySelector('.chat-messages').innerHTML = '';
    });
  })
}

function handlerChatList(data) {
  const chatListHTML = data.map(chat => {
    return generateChatList(chat);
  }).join('')
  document.querySelector('.chat-list').insertAdjacentHTML('afterbegin', chatListHTML);
}

function handlerUserInfo() {
  const userInfoHTML = generateUserInfo()
  document.querySelector('.user-info').innerHTML = userInfoHTML
}

function handlerListMessages(data) {
  const messagesHTML = data.map(message => {
    message.created = formatDate(message.created);
    return generateMessageList(message)
  }).join('')
  document.querySelector('.chat-messages').insertAdjacentHTML('afterbegin', messagesHTML)
}

function handlerSearch(event) {
  const searchValue = $('#search')[0].value
  $('.chat-list')[0].innerHTML = ''
  getChatList(query=searchValue)
}

function handlerEndlessPagination(data) {
  const scrollTop = $('.chat-messages').scrollTop()
  // сохраняем выосту дива для последующего расчета позиции при загрузки новой переписки
  divScrollHeight = $('.chat-messages')[0].scrollHeight
  const pageNumber = data[data.indexOf('page=')+5]
  if (scrollTop <= 10) {
    $('.chat-messages').off('scroll')
    // снимаем обработчик
    getMessages(event, page=pageNumber)
  }
}

function generateChatList(chat) {
  return `
    <li id=${chat.id} class="clearfix chats">
      <img src="https://bootdey.com/img/Content/avatar/avatar1.png" alt="avatar">
      <div class="about">
          <div class="name">${chat.name}</div>
          <div class="status"> <i class="fa fa-circle offline"></i> left 7 mins ago </div>
      </div>
    </li>
  `
}

function generateUserInfo() {
  return `
  <a href="javascript:void(0);" data-toggle="modal" data-target="#view_info">
    <img src="https://bootdey.com/img/Content/avatar/avatar2.png" alt="avatar">
  </a>
  <div class="chat-about">
    <h6 class="m-b-0">${activeChatUserName}</h6>
    <small>Last seen: 2 hours ago</small>
  </div>
  `
}

function generateMessageList(message) {
  if (message.author == authUserId) {
    return `
    <div class="chat-message-right pb-4">
      <div>
        <img src="https://bootdey.com/img/Content/avatar/avatar1.png" class="rounded-circle mr-1" alt="${authUserName}" width="40" height="40">
        <div class="text-muted small text-nowrap mt-2">${message.created} </div>
      </div>
      <div class="flex-shrink-1 bg-light rounded py-2 px-3 mr-3">
        <div class="font-weight-bold mb-1">${authUserName}</div>
        ${message.body}
      </div>
    </div>
    `
  } else {
    return `
    <div class="chat-message-left pb-4">
      <div>
        <img src="https://bootdey.com/img/Content/avatar/avatar1.png" class="rounded-circle mr-1" alt="ANOTHER NAME" width="40" height="40">
        <div class="text-muted small text-nowrap mt-2">${message.created} </div>
      </div>
      <div class="flex-shrink-1 bg-light rounded py-2 px-3 mr-3">
        <div class="font-weight-bold mb-1">${activeChatUserName} </div>
        ${message.body}
      </div>
    </div>
    `
  }
}