// LocalStorageとStreamlitの連携用JavaScript
// 会話履歴の保存と読み込み機能

// Streamlitとの通信
const sendMessageToStreamlit = (type, data = {}) => {
    const message = {
        type: type,
        ...data
    };
    window.parent.postMessage(message, '*');
};

// LocalStorageからの会話履歴の読み込み
const loadConversationFromStorage = () => {
    try {
        const data = localStorage.getItem('geminiConversation');
        return data ? JSON.parse(data) : [];
    } catch (e) {
        console.error('LocalStorageからの読み込みエラー:', e);
        return [];
    }
};

// LocalStorageへの会話履歴の保存
const saveConversationToStorage = (conversation) => {
    try {
        localStorage.setItem('geminiConversation', JSON.stringify(conversation));
    } catch (e) {
        console.error('LocalStorageへの保存エラー:', e);
    }
};

// 会話履歴のクリア
const clearConversationStorage = () => {
    try {
        localStorage.removeItem('geminiConversation');
    } catch (e) {
        console.error('LocalStorageのクリアエラー:', e);
    }
};

// Streamlitからのメッセージ受信
window.addEventListener('message', (e) => {
    if (e.data.type === 'GET_CONVERSATION') {
        const conversation = loadConversationFromStorage();
        sendMessageToStreamlit('CONVERSATION_DATA', { conversation });
    } else if (e.data.type === 'SAVE_CONVERSATION' && e.data.conversation) {
        saveConversationToStorage(e.data.conversation);
    } else if (e.data.type === 'CLEAR_CONVERSATION') {
        clearConversationStorage();
    }
});

// 初期化時に会話履歴を読み込んでStreamlitに送信
document.addEventListener('DOMContentLoaded', () => {
    const conversation = loadConversationFromStorage();
    sendMessageToStreamlit('INIT_CONVERSATION', { conversation });
}); 