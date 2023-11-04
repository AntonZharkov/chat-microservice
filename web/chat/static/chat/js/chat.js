$(function () {
  getChatList();
  setInterval(updateTimeOffline, 60000)
});

let currentChat
let activeChatUserName
let activeChatUserAvatar
let divScrollHeight

// Обработчик события выбора файла
$("#file-input, #image-input").on("change", handlerShowUploadedFile)

// Обработчик события отмены загрузки
$("#cancel-upload").on("click", handlerCancelUploadedFile)

function getChatList (query='') {
  $.ajax({
    url: `/api/v1/chat/chatlist/?search=${query}`,
    type: 'GET',
    success: function (data) {
      const chatListHTML = data.map(chat => {
        return generateChatHTML(chat);
      }).join('')
      document.querySelector('.chat-list').insertAdjacentHTML('afterbegin', chatListHTML);

      // чтобы не множить количество обработчиков мы удаляем старый и привязываем новый
      $('.chats').off('click').on('click', getMessages)
      $('#search').off('input').one('input', debouncedHandlerSearch)
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
  // удаляем бейджи с количеством непрочитанных сообщений
  $(`#${chatId} span.badge`).remove();
  // снимаем обработчик
  $('.chat-messages').off('scroll')
  $.ajax({
    url: `/api/v1/chat/messages/${chatId}/?page=${pageNumber}`,
    type: 'GET',
    success: function(data) {
      handlerUserNameTitle()
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
    hour12: true,
    day: 'numeric',
    month: 'long',
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
    activeChatUserAvatar = selectedItem.querySelector('img').src;
    document.querySelector('.chat-messages').innerHTML = '';
    });
  })
}

function handlerShowUploadedFile(event) {
  const fileName = event.target.files[0].name;
  $("#selected-file-name").text(fileName);
  $("#cancel-upload").show();
}

function handlerCancelUploadedFile(event) {
  $("#file-input").val("");
  $("#selected-file-name").text("");
  $("#cancel-upload").hide();
}

function handlerUserNameTitle() {
  const userNameTitleHTML = generateUserNameTitle()
  document.querySelector('.user-info').innerHTML = userNameTitleHTML
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

// обертка для вызова функции спустя заданное время
function debounce(func, delay) {
  let timeout;
  return function() {
    const context = this;
    const args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), delay);
  };
}

function updateTimeOffline() {
  $('.status .offline').each(function() {
    const parentStatusElement = $(this).closest('.status');
    const parentStatusText = parentStatusElement.text().trim();
    const parentStatusWords = parentStatusText.split(' ');

    const minutes = parseInt(parentStatusWords[1]);
    const newMinutes = minutes + 1;
    parentStatusElement.html(`<i class="fa fa-circle offline"></i> left ${newMinutes} mins ago`);
  });
}

const debouncedHandlerSearch = debounce(handlerSearch, 1000);

function handlerEndlessPagination(data) {
  const scrollTop = $('.chat-messages').scrollTop()
  // сохраняем выcoту дива для последующего расчета позиции при загрузки новой переписки
  divScrollHeight = $('.chat-messages')[0].scrollHeight
  const pageNumber = data.match(/page=(\d+)/)[1]

  if (scrollTop <= 10) {
    getMessages(event, page=pageNumber)
  }
}

function generateChatHTML(chat) {
  const online = chat.status.online
  const onlineDate = chat.status.date
  let howLongOfflineMin

  if (onlineDate) {
    const currentTimeInMillis = new Date().getTime(); // Текущее время в миллисекундах
    const targetTimeInMillis = new Date(onlineDate).getTime(); // Определенная дата в миллисекундах
    const differenceInMillis =  currentTimeInMillis - targetTimeInMillis; // Разница в миллисекундах
    howLongOfflineMin = Math.floor(differenceInMillis / (1000 * 60)); // Разница в минутах
  }
  const currentTime = new Date();
  return `
    <li id=${chat.id} class="clearfix chats">
      <img src="${chat.avatar}" alt="avatar">
      <div class="about">
          <div class="name">${chat.name}</div>
          <div class="status"> <i class="fa fa-circle ${online ? 'online': 'offline'}"></i> ${online ? 'Online': howLongOfflineMin >= 0 ? `left ${howLongOfflineMin} mins ago`: 'Offline'}  </div>
      </div>
    </li>
  `
}

function generateUserNameTitle() {
  const status = $('.active .about .status').html()
  return `
  <a href="javascript:void(0);" data-toggle="modal" data-target="#view_info">
    <img src="${activeChatUserAvatar}" alt="avatar">
  </a>
  <div class="chat-about">
    <h6 class="m-b-0">${activeChatUserName}</h6>
    <small>${status}</small>
  </div>
  `
}

function generateMessageList(message) {
  const user = JSON.parse(localStorage.getItem('user'));
  if (message.author === user.id) {
    return `
    <div class="chat-message-right pb-4">
      <div>
        <img src="${user.avatar}" class="rounded-circle mr-1" alt="${user.full_name}" width="40" height="40">
        <div class="text-muted small text-nowrap mt-2">${message.created} </div>
      </div>
      <div class="flex-shrink-1 bg-light rounded py-2 px-3 mr-3">
        <div class="font-weight-bold mb-1">${user.full_name}</div>
        ${message.body}
      </div>
    </div>
    `
  } else {
    return `
    <div class="chat-message-left pb-4">
      <div>
        <img src="${activeChatUserAvatar}" class="rounded-circle mr-1" alt="${activeChatUserName}" width="40" height="40">
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
