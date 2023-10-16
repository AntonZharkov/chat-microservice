$(function () {
  checkChatUserId();
});

function checkChatUserId() {
  const url = new URL(window.location.href);
  const chatUserId = parseInt(url.searchParams.get('id'))

  $.ajax({
    url: `/api/v1/chat/initialization/`,
    type: "POST",
    dataType: 'json',
    contentType: "application/json",
    data: JSON.stringify({
      chat_user_id: chatUserId,
    }),
    success: function(data) {
      localStorage.setItem('user', JSON.stringify(data.user));
      window.location.replace(`/?chat_id=${data.chat_id}`);
    },
    error: function(error) {
      console.log(error);
    }
  })
}
