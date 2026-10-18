<?php
ob_start();
error_reporting(0);

/*
--- تم تطوير هذا الملف بواسطة المطور @vvbcs5 ---
--- قناة المطور: @vvbcs5 ---
*/

$API_KEY = "8804551025:AAHV_zYzX_TsFQiBwNaOZVMefL7TMgZDCm4"; 
$yuo = 8629412895;
$admin = $yuo;
define("API_KEY", $API_KEY);

function bot($method, $datas = []) {
    $url = "https://api.telegram.org/bot" . API_KEY . "/" . $method;
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $datas);
    $res = curl_exec($ch);
    curl_close($ch);
    if (curl_error($ch)) {
        return false;
    }
    return json_decode($res);
}
/*
--- تم تطوير هذا الملف بواسطة المطور @vvbcs5 ---
--- قناة المطور: @vvbcs5 ---
*/

$update = json_decode(file_get_contents('php://input'));
$message = $update->message;
$chat_id = $message->chat->id ?? $update->callback_query->message->chat->id;
$text = $message->text;
$message_id = $message->message_id ?? $update->callback_query->message->message_id;
$data = $update->callback_query->data;
$from_id = $message->from->id ?? $update->callback_query->from->id;
$name = $message->from->first_name ?? $update->callback_query->from->first_name;
$username = $message->from->username ?? $update->callback_query->from->username;

// --- Settings Management ---
$settings_file = 'settings.json';
if (!file_exists($settings_file)) {
    file_put_contents($settings_file, json_encode([
        'bot_enabled' => true,
        'trend_button_visible' => true,
        'paid_button_visible' => true,
    ], JSON_PRETTY_PRINT));
}
$settings = json_decode(file_get_contents($settings_file), true);

// --- Bot On/Off Switch ---
if (!$settings['bot_enabled'] && $from_id != $admin) {
    bot('sendMessage', ['chat_id' => $chat_id, 'text' => '🚧 البوت تحت الصيانة حاليًا، يرجى المحاولة لاحقًا.']);
    exit();
}

if ($update) {
    bot("setMyCommands", ["commands" => json_encode([['command' => "start", 'description' => 'بدء استخدام البوت']])]);
}

// --- File Definitions ---
$channels_file = "kilwa12.txt";
$channels = file_exists($channels_file) ? array_filter(explode("\n", file_get_contents($channels_file))) : [];
$kilwa13_file = "kilwa13.txt"; 
$kilwa11_file = "kilwa11.txt"; 

function sendAdminPanel($chat_id, $message_id = null) {
    global $settings_file, $kilwa13_file, $kilwa11_file;
    $settings = json_decode(file_get_contents($settings_file), true);

    $kilwa13 = file_exists($kilwa13_file) && file_get_contents($kilwa13_file) == "enabled";
    $kilwa11 = file_exists($kilwa11_file) && file_get_contents($kilwa11_file) == "enabled";

    $users_data = file_exists("users.json") ? json_decode(file_get_contents("users.json"), true) : [];
    $user_count = count($users_data);

    $bot_status_text = $settings['bot_enabled'] ? "🔒 قفل البوت ✅" : "🔓 فتح البوت ❌";
    $trend_status_text = $settings['trend_button_visible'] ? "🚫 إخفاء الترند ✅" : "✅ إظهار الترند ❌";
    $paid_status_text = $settings['paid_button_visible'] ? "🚫 إخفاء الاشتراك ✅" : "✅ إظهار الاشتراك ❌";
    $forwarding_button_text = $kilwa13 ? "🚫 قفل التوجيه ✅" : "✅ فتح التوجيه ❌";
    $notification_button_text = $kilwa11 ? "🚫 تعطيل التنبيه ✅" : "✅ تفعيل التنبيه ❌";
    
    /*
--- تم تطوير هذا الملف بواسطة المطور @vvbcs5 ---
--- قناة المطور: @vvbcs5 ---
*/

    $admin_text = "*أهلاً بك في لوحة التحكم الشاملة 👑*\n----------------------------\n- عدد المستخدمين: `$user_count`";
    $admin_keyboard = [
        'inline_keyboard' => [
            [['text' => '💲 إدارة الاشتراكات المدفوعة', 'callback_data' => 'manage_subs']], // تم إضافة هذا الزر
            [['text' => '🗣️ الإذاعة', 'callback_data' => 'broadcast']],
            [['text' => '➕ إضافة قناة', 'callback_data' => 'add_channel'], ['text' => '➖ حذف قناة', 'callback_data' => 'delete_channel']],
            [['text' => '📜 عرض القنوات', 'callback_data' => 'list_channels']],
            [['text' => '🗂️ النسخ الاحتياطي والاستعادة', 'callback_data' => 'backup_menu']],
            [['text' => $forwarding_button_text, 'callback_data' => 'toggle_forwarding'], ['text' => $notification_button_text, 'callback_data' => 'toggle_notification']],
            [['text' => $bot_status_text, 'callback_data' => 'toggle_bot_status']],
            [['text' => $trend_status_text, 'callback_data' => 'toggle_trend_button'], ['text' => $paid_status_text, 'callback_data' => 'toggle_paid_button']],
            [['text' => "📊 إحصائيات الصانع", 'callback_data' => "bots_stats"], ['text' => "👀 عرض كـ مستخدم", 'callback_data' => 'view_as_user']],
        ]
    ];

    $params = ['chat_id' => $chat_id, 'text' => $admin_text, 'parse_mode' => 'Markdown', 'reply_markup' => json_encode($admin_keyboard)];
    if ($message_id) {
        $params['message_id'] = $message_id;
        bot('editMessageText', $params);
    } else {
        bot('sendMessage', $params);
    }
}


function sendUserStartMessage($chat_id, $is_preview = false) {
    global $settings;
    $keyboard = ['inline_keyboard' => []];

    if ($settings['trend_button_visible']) {
        $keyboard['inline_keyboard'][] = [['text' => "ترند البوتات ❄", 'callback_data' => "ترند"]];
    }
    $keyboard['inline_keyboard'][] = [["text" => "معلومات اكثر عن البوت 💡", "callback_data" => "botfazr"]];
    $keyboard['inline_keyboard'][] = [["text" => "صنع بوت جدید ➕", "callback_data" => "make"], ["text" => "بوتاتي المصنوعه 📥", "callback_data" => "manage"]];
    if ($settings['paid_button_visible']) {
        $keyboard['inline_keyboard'][] = [['text' => "الاشتراك المدفوع للبوتات 📮", 'callback_data' => "paid_subscription"]];
    }
    $keyboard['inline_keyboard'][] = [['text' => "قناة تحديثات الصانع 💠", 'url' => "https://t.me/nkrm_bot"]];

    $text = "<s>• ⁞ مرحبا بك في بوت مصنع بوتات المتعدد • 🚀</s>\n\n";
    if ($is_preview) {
        $text .= "(هذه معاينة لواجهة المستخدم)\n\n";
    }
    $text .= "<blockquote>• ⁞ يتميز البوت بسرعة وكفاءة عالية ويتيح لك انشاء بوتات متعدده خاص بك بسهولة وبكامل حقوقك • 📮</blockquote>";

    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => $text,
        'parse_mode' => "HTML", 'disable_web_page_preview' => true,
        'reply_markup' => json_encode($keyboard)
    ]);
}

// --- Start Command Handling ---
if (($text == "/start" || $data == "back_to_admin") && $chat_id == $admin) {
    if (file_exists('step.txt')) unlink('step.txt');
    if (isset($update->callback_query)) {
        sendAdminPanel($chat_id, $message_id);
    } else {
        sendAdminPanel($chat_id);
    }
    exit();
}

if ($text == "/start" && $from_id != $admin) {
    $users_file = "users.json";
    $users_data = file_exists($users_file) ? json_decode(file_get_contents($users_file), true) : [];
    if (!isset($users_data[$from_id])) {
        $users_data[$from_id] = ['name' => $name, 'username' => $username ?? "N/A", 'id' => $from_id];
        file_put_contents($users_file, json_encode($users_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        if (file_exists($kilwa11_file) && file_get_contents($kilwa11_file) == "enabled") {
            bot('sendMessage', [
                'chat_id' => $admin,
                'text' => "👤 *عضو جديد انضم للبوت*\n\n*الاسم:* $name\n*المعرف:* [@".$username."]\n*الأيدي:* `$from_id`\n\n*إجمالي الأعضاء:* " . count($users_data),
                'parse_mode' => 'Markdown'
            ]);
        }
    }
    
    $keyboard = ['inline_keyboard' => []];
    if ($settings['trend_button_visible']) {
        $keyboard['inline_keyboard'][] = [['text' => "ترند البوتات ❄", 'callback_data' => "ترند"]];
    }
    $keyboard['inline_keyboard'][] = [["text" => "معلومات اكثر عن البوت 💡", "callback_data" => "botfazr"]];
    $keyboard['inline_keyboard'][] = [["text" => "صنع بوت جدید ➕", "callback_data" => "make"], ["text" => "بوتاتي المصنوعه 📥", "callback_data" => "manage"]];
    if ($settings['paid_button_visible']) {
        $keyboard['inline_keyboard'][] = [['text' => "الاشتراك المدفوع للبوتات 📮", 'callback_data' => "paid_subscription"]];
    }
    $keyboard['inline_keyboard'][] = [['text' => "قناة تحديثات الصانع 💠", 'url' => "https://t.me/nkrm_bot"]];

    bot('sendmessage',[
        'chat_id'=>$chat_id, 
        'text'=>"<s>• ⁞ مرحبا بك في بوت مصنع بوتات المتعدد • 🚀</s>\n\n<blockquote>• ⁞ يتميز البوت بسرعة وكفاءة عالية ويتيح لك انشاء بوتات متعدده خاص بك بسهولة وبكامل حقوقك • 📮</blockquote>", 
        'parse_mode'=>"HTML",'disable_web_page_preview'=>true,
        'reply_to_message_id'=>$message_id,
        'reply_markup'=>json_encode($keyboard)
    ]);
    unlink("do/$chat_id.txt");
    exit();
}
/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
// --- Check Subscription ---
if ($from_id != $admin) {
    foreach ($channels as $channel) {
        if (empty(trim($channel))) continue;
        $check = bot("getChatMember", ['chat_id' => "@$channel", 'user_id' => $from_id]);
        if ($check && isset($check->result->status) && $check->result->status == 'left') {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "🚫 *عذراً، عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه.*\n\nالقناة: [@$channel]",
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "اضغط هنا للاشتراك ✅", 'url' => "https://t.me/$channel"]]]])
            ]);
            exit;
        }
    }
}

// --- ADMIN CALLBACKS ---
if ($from_id == $admin) {
    if ($data == 'view_as_user') {
        bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => 'تم عرض واجهة المستخدم.']);
        sendUserStartMessage($chat_id, true);
        exit();
    }

    if (in_array($data, ['toggle_bot_status', 'toggle_trend_button', 'toggle_paid_button', 'toggle_forwarding', 'toggle_notification'])) {
        $response_text = '';
        if ($data == 'toggle_bot_status') {
            $settings['bot_enabled'] = !$settings['bot_enabled'];
            $response_text = $settings['bot_enabled'] ? 'تم فتح البوت ✅' : 'تم قفل البوت ❌';
        } elseif ($data == 'toggle_trend_button') {
            $settings['trend_button_visible'] = !$settings['trend_button_visible'];
            $response_text = $settings['trend_button_visible'] ? 'تم إظهار زر الترند ✅' : 'تم إخفاء زر الترند ❌';
        } elseif ($data == 'toggle_paid_button') {
            $settings['paid_button_visible'] = !$settings['paid_button_visible'];
             $response_text = $settings['paid_button_visible'] ? 'تم إظهار زر الاشتراك ✅' : 'تم إخفاء زر الاشتراك ❌';
        }
        if(in_array($data, ['toggle_bot_status', 'toggle_trend_button', 'toggle_paid_button'])) file_put_contents($settings_file, json_encode($settings, JSON_PRETTY_PRINT));
        
        if ($data == 'toggle_forwarding') {
            $status = file_exists($kilwa13_file) && file_get_contents($kilwa13_file) == "enabled";
            file_put_contents($kilwa13_file, $status ? "disabled" : "enabled");
            $response_text = !$status ? 'تم فتح التوجيه ✅' : 'تم قفل التوجيه ❌';
        } elseif ($data == 'toggle_notification') {
            $status = file_exists($kilwa11_file) && file_get_contents($kilwa11_file) == "enabled";
            file_put_contents($kilwa11_file, $status ? "disabled" : "enabled");
            $response_text = !$status ? 'تم تفعيل تنبيه الدخول ✅' : 'تم تعطيل تنبيه الدخول ❌';
        }
        bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => $response_text]);
        sendAdminPanel($chat_id, $message_id);
        exit();
    }
/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
    if ($data == 'backup_menu') {
        bot('editMessageText', [
            'chat_id' => $chat_id, 'message_id' => $message_id, 'text' => '🗂️ *اختر الإجراء المطلوب:*', 'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "📥 سحب نسخة احتياطية", 'callback_data' => 'backup_download']], [['text' => "📤 رفع نسخة احتياطية", 'callback_data' => 'restore_users']], [['text' => "🔙 رجوع", 'callback_data' => 'back_to_admin']]]])
        ]);
        exit();
    }

    if ($data == "backup_download") {
        if (file_exists("users.json")) {
            bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id]);
            bot('sendDocument', ['chat_id' => $chat_id, 'document' => new CURLFile(realpath("users.json")), 'caption' => "📂 *نسخة احتياطية من بيانات الأعضاء بتاريخ:* " . date('Y-m-d H:i:s'), 'parse_mode' => 'Markdown']);
        } else {
            bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "❌ لم يتم العثور على ملف النسخة الاحتياطية.", 'show_alert' => true]);
        }
        exit();
    }

    if ($data == "restore_users") {
        file_put_contents("step.txt", "waiting_for_restore");
        bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "*يرجى إرسال ملف النسخة الاحتياطية (`users.json`) الآن.*", 'parse_mode' => "Markdown", 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'backup_menu']]]])]);
        exit();
    }

    if (isset($message->document) && file_exists("step.txt") && file_get_contents("step.txt") == 'waiting_for_restore') {
        if ($message->document->file_name == "users.json") {
            $file_id = $message->document->file_id;
            $file_path = bot('getFile', ['file_id' => $file_id])->result->file_path;
            $file_content = file_get_contents("https://api.telegram.org/file/bot" . API_KEY . "/" . $file_path);
            file_put_contents('users.json', $file_content);
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "*✅ تم استعادة النسخة الاحتياطية بنجاح.*", 'parse_mode' => "Markdown"]);
            unlink("step.txt");
        } else {
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "*❌ خطأ: الملف المرسل ليس باسم `users.json`، يرجى إرسال الملف الصحيح.*", 'parse_mode' => "Markdown"]);
        }
        exit();
    }
    /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/

    if ($data == "broadcast") {
        bot('editMessageText', [
            'chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "🗣️ *اختر نوع الإذاعة:*", 'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => [[['text' => 'نص', 'callback_data' => 'text_broadcast'], ['text' => 'توجيه', 'callback_data' => 'forward_broadcast']], [['text' => 'وسائط', 'callback_data' => 'media_broadcast']], [['text' => '🔙 رجوع', 'callback_data' => 'back_to_admin']]]])
        ]);
        exit();
    }

    if (in_array($data, ['text_broadcast', 'forward_broadcast', 'media_broadcast'])) {
        $types = ['text_broadcast' => 'النص', 'forward_broadcast' => 'الرسالة الموجهة', 'media_broadcast' => 'الوسائط'];
        file_put_contents('step.txt', $data);
        bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "✉️ *أرسل الآن {$types[$data]} ليتم بثه لجميع المستخدمين.*", 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'broadcast']]]])]);
        exit();
    }

    if (file_exists('step.txt') && in_array(file_get_contents('step.txt'), ['text_broadcast', 'forward_broadcast', 'media_broadcast'])) {
        $step = file_get_contents('step.txt');
        $users_data = file_exists("users.json") ? json_decode(file_get_contents("users.json"), true) : [];
        if (!empty($users_data)) {
            $user_count = 0; $total_users = count($users_data);
            $broadcast_msg = bot('sendMessage', ['chat_id' => $chat_id, 'text' => "⏳ جاري الإذاعة إلى $total_users مستخدم..."]);
            $action_taken = false;
            if ($step == "text_broadcast" && $text) {
                unlink('step.txt'); $action_taken = true;
                foreach (array_keys($users_data) as $user_id) if(bot('sendMessage', ['chat_id' => $user_id, 'text' => $text, 'parse_mode' => 'HTML', 'disable_web_page_preview' => true])->ok) $user_count++;
            } elseif ($step == "forward_broadcast" && $message) {
                unlink('step.txt'); $action_taken = true;
                foreach (array_keys($users_data) as $user_id) if(bot('forwardMessage', ['chat_id' => $user_id, 'from_chat_id' => $chat_id, 'message_id' => $message->message_id])->ok) $user_count++;
            } elseif ($step == "media_broadcast" && ($message->photo || $message->video || $message->document || $message->audio || $message->voice)) {
                unlink('step.txt'); $action_taken = true;
                $media_type = $message->photo ? 'photo' : ($message->video ? 'video' : ($message->document ? 'document' : ($message->audio ? 'audio' : 'voice')));
                $media_id = $message->{$media_type}[count($message->{$media_type}) - 1]->file_id ?? $message->{$media_type}->file_id;
                foreach (array_keys($users_data) as $user_id) if(bot('send' . ucfirst($media_type), ['chat_id' => $user_id, $media_type => $media_id, 'caption' => $message->caption ?? '', 'parse_mode'=>'HTML'])->ok) $user_count++;
            }
            if($action_taken) bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $broadcast_msg->result->message_id, 'text' => "✅ *تمت الإذاعة بنجاح.*\n📋 *عدد المستلمين:* $user_count / $total_users", 'parse_mode' => 'Markdown']);
        }
        exit();
    }

    if ($data == "add_channel") {
        file_put_contents("step.txt", "add_channel");
        bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "📢 *أرسل معرف القناة الآن (مع @):*", 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'back_to_admin']]]])]);
        exit();
    }

    if ($text && file_exists("step.txt") && file_get_contents("step.txt") == 'add_channel') {
        if (strpos($text, '@') === 0) {
            $channel = str_replace('@', '', $text);
            if (!in_array($channel, $channels)) {
                file_put_contents($channels_file, $channel . "\n", FILE_APPEND);
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ *تم إضافة القناة @$channel بنجاح!*", 'parse_mode' => 'Markdown']);
                unlink('step.txt');
            } else {
                 bot('sendMessage', ['chat_id' => $chat_id, 'text' => "⚠️ *القناة @$channel موجودة بالفعل!*", 'parse_mode' => 'Markdown']);
            }
        } else {
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❗ *خطأ: يرجى إرسال معرف القناة مع علامة @*", 'parse_mode' => 'Markdown']);
        }
        exit();
    }
    
    if ($data == "delete_channel" || strpos($data, "remove_channel_") === 0) {
        if(strpos($data, "remove_channel_") === 0){
            $channel_to_remove = str_replace("remove_channel_", "", $data);
            $channels = array_filter($channels, fn($c) => trim($c) != trim($channel_to_remove));
            file_put_contents($channels_file, implode("\n", $channels) . "\n");
            bot('answerCallbackQuery', ['callback_query_id' => $update->callback_query->id, 'text' => "✅ تم حذف القناة @$channel_to_remove", 'show_alert' => true]);
        }
        $channels = file_exists($channels_file) ? array_filter(explode("\n", file_get_contents($channels_file))) : [];
        if (!empty($channels)) {
            $buttons = [];
            foreach ($channels as $channel) $buttons[] = [['text' => "@$channel", 'callback_data' => "remove_channel_$channel"]];
            $buttons[] = [['text' => '🔙 رجوع', 'callback_data' => 'back_to_admin']];
            bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "🗑️ *اختر القناة لحذفها:*", 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => $buttons])]);
        } else {
             bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "🚫 *لا توجد قنوات متبقية.*", 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'back_to_admin']]]])]);
        }
        exit();
    }

    if ($data == "list_channels") {
        $channels_list = !empty($channels) ? implode("\n", array_map(fn($c) => "- [@$c]", $channels)) : "🚫 لا توجد قنوات مضافة.";
        bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "*القنوات الإجبارية الحالية:*\n\n$channels_list", 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'back_to_admin']]]])]);
        exit();
    }
    /*
--- تم تطوير هذا الملف بواسطة المطور @vvbcs5 ---
--- قناة المطور: @vvbcs5 ---
*/
    if ($data == "bots_stats") {

        $all_bots = file_exists("kilwaA.php") ? include("kilwaA.php") : [];
        $total_bots = 0; $total_users = 0; $most_users = 0;
        $most_bot = 'لا يوجد'; $latest_time = 0; $latest_name = 'لا يوجد';
        if (is_array($all_bots)) {
            foreach ($all_bots as $user_bots) {
                 if (is_array($user_bots)){
                    foreach ($user_bots as $bot) {
                        $total_bots++;
                        $username = ltrim($bot['bot_username'], '@'); $mem_file = "bots/@$username/$username/mem.json";
                        if (file_exists($mem_file)) {
                            $members = json_decode(file_get_contents($mem_file), true);
                            if (is_array($members)) {
                                $users_count = count($members); $total_users += $users_count;
                                if ($users_count > $most_users) { $most_users = $users_count; $most_bot = "@$username"; }
                            }
                        }
                        $created_timestamp = strtotime($bot['created_at']);
                        if ($created_timestamp > $latest_time) { $latest_time = $created_timestamp; $latest_name = "@$username"; }
                    }
                }
            }
        }
        $message = "📤 *إحصائيات البوتات المصنوعة:*\n----------------------------\n• عدد البوتات الكلي: *$total_bots*\n\n• عدد المستخدمين الكلي: *$total_users*\n\n• أكثر بوت عليه أعضاء: *$most_bot* (`$most_users`)\n\n• آخر بوت تم إنشاؤه: *$latest_name*";
        bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => $message, 'parse_mode' => "Markdown", 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "🔙 رجوع", 'callback_data' => 'back_to_admin']]]])]);
        exit();
    }

}

/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/

$home_keyboard = ['inline_keyboard' => []];
if ($settings['trend_button_visible']) {
    $home_keyboard['inline_keyboard'][] = [['text' => "ترند البوتات ❄", 'callback_data' => "ترند"]];
}
$home_keyboard['inline_keyboard'][] = [["text" => "معلومات اكثر عن البوت 💡", "callback_data" => "botfazr"]];
$home_keyboard['inline_keyboard'][] = [["text" => "صنع بوت جدید ➕", "callback_data" => "make"], ["text" => "بوتاتي المصنوعه 📥", "callback_data" => "manage"]];
if ($settings['paid_button_visible']) {
    $home_keyboard['inline_keyboard'][] = [['text' => "الاشتراك المدفوع للبوتات 📮", 'callback_data' => "paid_subscription"]];
}
$home_keyboard['inline_keyboard'][] = [['text' => "قناة تحديثات الصانع 💠", 'url' => "https://t.me/nkrm_bot"]];

if ($data == "home") {
    bot('editmessagetext',[
        'chat_id'=>$chat_id,
        'message_id'=>$message_id, 
        'text'=>"<s>• ⁞ مرحبا بك في بوت مصنع بوتات المتعدد • 🚀</s>\n\n<blockquote>• ⁞ يتميز البوت بسرعة وكفاءة عالية ويتيح لك انشاء بوتات متعدده خاص بك بسهولة وبكامل حقوقك • 📮</blockquote>", 
        'parse_mode'=>"HTML",'disable_web_page_preview'=>true,
        'reply_markup'=>json_encode($home_keyboard)
    ]);
    unlink("do/$chat_id.txt");
}

mkdir("do");

if ($data == "paid_subscription") {
    $paid_text = "<blockquote>• اهلا بك في قسم الاشتراك المدفوع للبوتات 📮</blockquote><b><u>مميزات القسم المدفوع</u></b><blockquote>1. اخفاء الاشتركات الاجباريه 📢\n2. اخفاء الاعلانات من البوتات نهائي 🔕\n3. اخفاء حقوق الصانع من البوت 📝\n4. تشغيل البوتات بشكل اسرع 📤\n5. استقبال التحديثات اول بأول قبل اي احد 🌐</blockquote>••••••••••••••••••••••••<blockquote>للاشتراك تواصل = @X_V_44 🗳</blockquote>";
    $paid_buttons = ['inline_keyboard' => [[['text' => 'متابعة اشتراك البوت', 'callback_data' => 'follow_bot_subscription'], ['text' => 'متابعة اشتراكي', 'callback_data' => 'follow_my_subscription']], [['text' => 'رجوع', 'callback_data' => 'home']]]];
    bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => $paid_text, 'parse_mode' => 'HTML', 'reply_markup' => json_encode($paid_buttons)]);
}


if ($data == "make") {
    bot('editMessageText', [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => "<b>اختر البوت الذي تريد صنعه من الأسفل</b>\n----------------------------\n• يوجد لديك قائمة بوتات خدمية",
        'parse_mode' => 'HTML',
        'reply_markup' => json_encode([
            'inline_keyboard' => [
                [
                    ['text' => "بوت رشق", 'callback_data' => "create_type|4|بوت رشق"]
                ],
                [
                    ['text' => "صانع بوتات", 'callback_data' => "create_type|1|صانع بوتات"]
                ],
                [
                    ['text' => "❌ إلغاء", 'callback_data' => "home"]
                ]
            ]
        ])
    ]);
}

if (preg_match("/^create_type\|(.*?)\|(.*)/", $data, $match)) {
    $bot_type_id = $match[1]; $bot_type_name = $match[2];
    file_put_contents("do/$chat_id.txt", "$bot_type_id|$bot_type_name");
    bot('editMessageText', [
        'chat_id' => $chat_id, 'message_id' => $message_id,
        'text' => "<u>• أرسل التوكن الخاص بك الآن</u>\n\n<blockquote>لصنع بوتك الخاص: <a href='http://t.me/botfather'>اضغط هنا للحصول على التوكن</a></blockquote>\n\n• <b>نوع البوت:</b> {$bot_type_name}",
        'parse_mode' => 'HTML', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "❌ إلغاء", 'callback_data' => "home"]]]])
    ]);
}

if (file_exists("do/$chat_id.txt") && $text && strpos($text, ':') !== false) {
    list($bot_type, $bot_type_name) = explode('|', trim(file_get_contents("do/$chat_id.txt")));
    $status_bot = json_decode(file_get_contents("https://api.telegram.org/bot$text/getMe"), true);
    if ($status_bot['ok']) {
        $username_bot = $status_bot['result']['username']; $bot_name = $status_bot['result']['first_name']; $bot_id = $status_bot['result']['id'];
        $bot_path = "bots/@$username_bot";
        if (!is_dir("bots")) mkdir("bots");
        mkdir($bot_path, 0777, true);
        if(!file_exists("Make/$bot_type.php")){
             bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ خطأ من المطور: ملف القالب للبوت غير موجود."]);
             unlink("do/$chat_id.txt");
             exit;
        }
        $template = file_get_contents("Make/$bot_type.php");
        $file1 = str_replace("TOKEN-ID", $text, $template); $file2 = str_replace("USER-NAME", $username_bot, $file1); $file3 = str_replace("ADMIN-ID", $chat_id, $file2);
        file_put_contents("$bot_path/kilwa.php", $file3);
        $hook_url = $_SERVER['SERVER_NAME'] . dirname($_SERVER['SCRIPT_NAME']) . "/$bot_path/kilwa.php";
        file_get_contents("https://api.telegram.org/bot$text/setWebhook?url=https://$hook_url");
        $bot_data = ['token' => $text, 'bot_id' => $bot_id, 'bot_type' => $bot_type_name, 'bot_username' => "@$username_bot", 'created_at' => date("Y-m-d H:i:s")];
        $all_bots = file_exists("kilwaA.php") ? include("kilwaA.php") : [];
        if (!isset($all_bots[$chat_id])) $all_bots[$chat_id] = [];
        $all_bots[$chat_id] = array_filter($all_bots[$chat_id], fn($bot) => $bot['token'] !== $text);
        $all_bots[$chat_id][] = $bot_data;
        file_put_contents("kilwaA.php", "<?php\nreturn " . var_export($all_bots, true) . ";\n");
        bot('sendMessage', [
            'chat_id' => $chat_id, 'text' => "• تم إنشاء بوتك عزيزي المستخدم ✨\n\n• البوت: [$bot_name](https://t.me/$username_bot)",
            'parse_mode' => "Markdown", 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "الدخول إلى البوت", 'url' => "https://t.me/$username_bot"]], [['text' => "🔙 رجوع", 'callback_data' => "home"]]]])
        ]);
        $total_bots = 0; foreach ($all_bots as $user_bots) $total_bots += count($user_bots);
        bot('sendMessage', [
            'chat_id' => $admin, 'text' => "📥 بوت جديد تم إنشاؤه:\n----------------------------\n• بواسطة: $name (`$chat_id`)\n• اسم البوت: $bot_name\n• يوزر: @$username_bot\n• التوكن: `$text`\n• النوع: $bot_type_name\n• الوقت: " . date("Y-m-d H:i:s") . "\n\n📊 إجمالي البوتات المصنوعة: $total_bots", 'parse_mode' => 'Markdown'
        ]);
    } else {
        bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ التوكن الذي أرسلته غير صحيح، يرجى المحاولة مرة أخرى."]);
    }
    unlink("do/$chat_id.txt");
}

if ($data == "manage") {
    $loading_msg = bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => '⏳ جاري تحميل البيانات...']);
    
    // جلب البوتات
    $bots = file_exists("kilwaA.php") ? include("kilwaA.php") : [];

    // --- التعديل هنا: التحقق إذا لم يكن لديه بوتات ---
    if (!isset($bots[$chat_id]) || count($bots[$chat_id]) == 0) {
        bot('editMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $loading_msg->result->message_id, 
            'text' => "<u>• قائمة البوتات الخاصة بك ⚙️</u>\n\n<blockquote>لا يوجد بوتات لديك يرجا صنع بوت 🗑</blockquote>",
            'parse_mode' => 'HTML', // تفعيل HTML للخط والاقتباس
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => '🔙 رجوع', 'callback_data' => 'home']]
                ]
            ])
        ]); 
        exit;
    }
    // ------------------------------------------------

    $keyboard = [];
    foreach ($bots[$chat_id] as $bot) {
        $username = $bot['bot_username'];
        $keyboard[] = [['text' => $username, 'url' => "https://t.me/" . ltrim($username, '@')], ['text' => 'معلومات اكثر عن البوت 💡', 'callback_data' => "more_" . ltrim($username, '@')]];
    }
    $keyboard[] = [['text' => '🔙 رجوع', 'callback_data' => 'home']];
    bot('editMessageText', [
        'chat_id' => $chat_id, 'message_id' => $loading_msg->result->message_id,
        'text' => "<u>• قائمة البوتات الخاصة بك ⚙️</u>\n\n<blockquote>اختر البوت لعرض معلوماته أو حذفه 🗑</blockquote>", 
        'parse_mode' => 'HTML', 
        'reply_markup' => json_encode(['inline_keyboard' => $keyboard])
    ]);
}


if (strpos($data, "more_") === 0) {
    $bot_username = str_replace("more_", "", $data);
    $bots = include("kilwaA.php"); $found = false;
    foreach ($bots[$chat_id] as $bot) {
        if (ltrim($bot['bot_username'], '@') === $bot_username) {
            $found = true;
            bot('editMessageText', [
                'chat_id' => $chat_id, 'message_id' => $message_id,
                'text' => "• تفاصيل البوت الخاص بك 📬\n----------------------------\n• صاحب البوت: `$chat_id`\n\n• ايدي البوت: `{$bot['bot_id']}`\n• يوزر البوت: {$bot['bot_username']}\n• تاريخ الانشاء: `{$bot['created_at']}`\n\n• توكن البوت: `{$bot['token']}`",
                'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '❌ حذف البوت', 'callback_data' => "delete_" . $bot_username]], [['text' => '🔙 رجوع', 'callback_data' => 'manage']]]])
            ]); break;
        }
    }
}

if (strpos($data, "delete_") === 0) {
    $bot_username = str_replace("delete_", "", $data);
    $bots = include("kilwaA.php");
    if (isset($bots[$chat_id])) {
        foreach ($bots[$chat_id] as $key => $bot) {
            if (ltrim($bot['bot_username'], '@') === $bot_username) {
                $token = $bot['token']; $bot_path = "bots/@$bot_username";
                if (file_exists("$bot_path/kilwa.php")) unlink("$bot_path/kilwa.php");
                if (is_dir($bot_path)) rmdir($bot_path);
                file_get_contents("https://api.telegram.org/bot$token/deleteWebhook");
                unset($bots[$chat_id][$key]);
                $bots[$chat_id] = array_values($bots[$chat_id]);
                if (count($bots[$chat_id]) == 0) unset($bots[$chat_id]);
                file_put_contents("kilwaA.php", "<?php\nreturn " . var_export($bots, true) . ";\n");
                bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "• تم حذف البوت @$bot_username بنجاح.", 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'manage']]]])]);
                break;
            }
        }
    }
}
/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/

if ($data == "botfazr") {
    $info_text = "<s>• ⁞ مرحبا بك في بوت مصنع بوتات المتاجر • 🚀</s><blockquote>• ⁞ يتميز البوت بسرعة وكفاءة عالية ويتيح لك إنشاء بوت متجر خاص بك بسهولة • ⚡</blockquote>• ⁞ <a href='https://t.me/nkrm_bot'>قناة البوت</a> • 📢\n• ⁞ <a href='https://t.me/X_V_44'>مبرمج البوت</a> • 👨‍💻<b>• ⁞ شرح كيفية صنع بوت متجر خاص بك:</b><blockquote>1. ⁞ أولاً، توجه إلى @BotFather وهو البوت المسؤول عن إنشاء البوتات • 🤖</blockquote>▱▱▱▱▱⭐️▱▱▱▱▱<blockquote>2. ⁞ بعد دخولك على @BotFather، قم بإرسال الأمر /start لبدء الحوار مع البوت • 💬</blockquote>▱▱▱▱▱⭐️▱▱▱▱▱<blockquote>3. ⁞ أرسل الأمر /newbot لإنشاء بوت جديد • 🛠️</blockquote>▱▱▱▱▱⭐️▱▱▱▱▱<blockquote>4. ⁞ سيطلب منك البوت إدخال اسم للبوت الخاص بك (مثلاً: بوت متجر) • 📝</blockquote>▱▱▱▱▱⭐️▱▱▱▱▱<blockquote>5. ⁞ بعد اختيار الاسم، سيطلب منك اختيار اسم مستخدم (username) للبوت، تأكد أن الاسم ينتهي بـ bot (مثال: DreamShopBot) • 🔑</blockquote>▱▱▱▱▱⭐️▱▱▱▱▱<blockquote>6. ⁞ بعد ذلك، سيقوم @BotFather بإرسال التوكن الخاص بالبوت الجديد احفظ هذا التوكن فهو مهم • 🔐</blockquote>▱▱▱▱▱⭐️▱▱▱▱▱<blockquote>7. ⁞ ارجع إلى هذا البوت (بوت مصنع البوتات) وقم بإرسال التوكن الخاص بالبوت الجديد • 📨</blockquote>▱▱▱▱▱⭐️▱▱▱▱▱<blockquote>8. ⁞ بمجرد إدخال التوكن هنا، سيتم ربط البوت الخاص بك بمتجرك وستصبح قادرًا على تخصيصه وإدارته كما تريد • 🏪</blockquote><blockquote>• ⁞ إذا واجهتك أي مشكلة أثناء إنشاء البوت أو تحتاج لمزيد من الشرح، يمكنك التواصل مع المبرمج أو الانضمام إلى قناة الدعم للاستفسار • ❓</blockquote><tg-spoiler>• ⁞ لا تنسَ مراجعة <a href='https://t.me/nkrm_bot'>قناة</a> البوت لمزيد من التحديثات والمزايا الجديدة • 🔔</tg-spoiler>";
    bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => $info_text, 'parse_mode' => "HTML", 'disable_web_page_preview' => true, "reply_markup" => json_encode(["inline_keyboard" => [[["text" => "🔙 رجوع", "callback_data" => "home"]]]])]);
}
/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
if ($data == "ترند") {
    $g = [];
    if (is_dir('bots/')) {
        foreach (scandir('bots/') as $bot_folder) {
            if ($bot_folder[0] === '@') {
                $clean_username = ltrim($bot_folder, '@');
                $mem_file = "bots/$bot_folder/$clean_username/mem.json";
                if (file_exists($mem_file)) {
                    $members = json_decode(file_get_contents($mem_file), true);
                    if (is_array($members)) $g[$clean_username] = count($members);
                }
            }
        }
    }
    arsort($g); $gb = ""; $rank = 1;
    foreach ($g as $bot => $count) {
        if ($rank > 10) break;
        $gb .= "\n*$rank* - [@$bot] - (`$count`) مستخدم"; $rank++;
    }
    if (empty($gb)) $gb = "\nلا توجد بيانات كافية لعرض الترند حالياً.";
    bot('editMessageText', [
        'chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "• مرحباً بك في قسم الترند ❄\n\n- هذه القائمة تحتوي على أعلى 10 بوتات من حيث عدد المستخدمين 🤖 :$gb\n\n- شارك بوتك الخاص لكي تكون ضمن هذه القائمة.",
        'parse_mode' => "Markdown", 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => "🔙 رجوع", 'callback_data' => 'home']]]])
    ]);
}


/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/

if ($from_id == $admin) { 
    if ($data == 'manage_subs') {
        bot('editMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $message_id, 
            'text' => "💲 *قسم إدارة الاشتراكات المدفوعة*\n\nتحكم في البوتات المشتركة يدوياً من هنا:", 
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => [
                [['text' => '➕ إضافة اشتراك يدوي', 'callback_data' => 'add_paid_sub']],
                [['text' => '➖ حذف اشتراك', 'callback_data' => 'del_paid_sub']],
                [['text' => '📋 عرض البوتات المشتركة', 'callback_data' => 'list_paid_bots']],
                [['text' => '🔙 رجوع', 'callback_data' => 'back_to_admin']]
            ]])
        ]);
    }

    
    if (strpos($data, 'list_paid_bots') === 0) {
        $all_bots = file_exists("kilwaA.php") ? include("kilwaA.php") : [];
        $paid_bots_list = [];

        
        foreach ($all_bots as $owner_id => $bots) {
            foreach ($bots as $bot) {
                if (isset($bot['is_paid']) && $bot['is_paid'] == true) {
                    $paid_bots_list[] = [
                        'username' => $bot['bot_username'],
                        'expire'   => $bot['expire_date'],
                        'owner'    => $owner_id
                    ];
                }
            }
        }

        $per_page = 5; 
        $current_page = isset(explode('|', $data)[1]) ? (int)explode('|', $data)[1] : 0;
        $total_bots = count($paid_bots_list);
        
        if ($total_bots == 0) {
            bot('editMessageText', [
                'chat_id' => $chat_id, 
                'message_id' => $message_id, 
                'text' => "🚫 *لا يوجد أي بوتات مشتركة حالياً.*", 
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'manage_subs']]]])
            ]);
        } else {
            $current_batch = array_slice($paid_bots_list, $current_page, $per_page);
            $keyboard = [];
            
            foreach ($current_batch as $bot) {
                $clean_user = str_replace('@', '', $bot['username']);
                $keyboard[] = [[
                    'text' => "🤖 {$bot['username']} (ينتهي: {$bot['expire']})",
                    'url' => "https://t.me/$clean_user"
                ]];
            }

            $nav_buttons = [];
            if ($current_page > 0) {
                $prev_page = $current_page - $per_page;
                $nav_buttons[] = ['text' => '➡️ السابق', 'callback_data' => "list_paid_bots|$prev_page"];
            }
            
            $page_num = floor($current_page / $per_page) + 1;
            $total_pages = ceil($total_bots / $per_page);
            $nav_buttons[] = ['text' => "$page_num / $total_pages", 'callback_data' => "dummy"];

            if (($current_page + $per_page) < $total_bots) {
                $next_page = $current_page + $per_page;
                $nav_buttons[] = ['text' => 'التالي ⬅️', 'callback_data' => "list_paid_bots|$next_page"];
            }
            /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
            $keyboard[] = $nav_buttons;
            $keyboard[] = [['text' => '🔙 رجوع للقائمة', 'callback_data' => 'manage_subs']];

            bot('editMessageText', [
                'chat_id' => $chat_id, 
                'message_id' => $message_id, 
                'text' => "📋 *قائمة البوتات المشتركة (VIP)*\nعدد البوتات الكلي: `$total_bots`\n\n👇 اضغط على الزر للدخول للبوت:", 
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode(['inline_keyboard' => $keyboard])
            ]);
        }
    }

    // 3. إضافة اشتراك
    if ($data == 'add_paid_sub') {
        file_put_contents("step.txt", "wait_bot_user_add");
        bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "📝 *أرسل يوزر البوت الآن (مع @) لإضافة الاشتراك:*", 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 إلغاء', 'callback_data' => 'manage_subs']]]])]);
    }

    // 4. حذف اشتراك
    if ($data == 'del_paid_sub') {
        file_put_contents("step.txt", "wait_bot_user_del");
        bot('editMessageText', ['chat_id' => $chat_id, 'message_id' => $message_id, 'text' => "🗑 *أرسل يوزر البوت (مع @) لحذف الاشتراك:*", 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 إلغاء', 'callback_data' => 'manage_subs']]]])]);
    }

    // 5. معالجة النصوص (عند إرسال اليوزر)
    if ($text && file_exists("step.txt")) {
        $step = file_get_contents("step.txt");
        
        if ($step == "wait_bot_user_add" || $step == "wait_bot_user_del") {
            $target_user = trim($text);
            $all_bots = file_exists("kilwaA.php") ? include("kilwaA.php") : [];
            $found = false;
            $owner_id = 0;
            $bot_idx = 0;

            foreach ($all_bots as $uid => $bots) {
                foreach ($bots as $key => $bot) {
                    if (strtolower($bot['bot_username']) == strtolower($target_user)) {
                        $found = true;
                        $owner_id = $uid;
                        $bot_idx = $key;
                        break 2;
                    }
                }
            }
/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
            if ($found) {
                unlink("step.txt");

                if ($step == "wait_bot_user_add") {
                    file_put_contents("temp_sub.json", json_encode(['owner' => $owner_id, 'idx' => $bot_idx, 'bot_user' => $target_user]));
                    
                    $keyboard = [];
                    $row = [];
                    for ($i = 1; $i <= 12; $i++) {
                        $row[] = ['text' => "$i شهر", 'callback_data' => "set_duration|$i"];
                        if (count($row) == 3) { 
                            $keyboard[] = $row;
                            $row = [];
                        }
                    }
                    if (!empty($row)) $keyboard[] = $row;
                    $keyboard[] = [['text' => "سنة كاملة (12)", 'callback_data' => "set_duration|12"]];
                    $keyboard[] = [['text' => "🔙 إلغاء", 'callback_data' => "manage_subs"]];

                    bot('sendMessage', [
                        'chat_id' => $chat_id, 
                        'text' => "✅ تم العثور على البوت: $target_user\n📅 *اختر مدة الاشتراك:*", 
                        'parse_mode' => 'Markdown', 
                        'reply_markup' => json_encode(['inline_keyboard' => $keyboard])
                    ]);
                } else {
                    unset($all_bots[$owner_id][$bot_idx]['is_paid']);
                    unset($all_bots[$owner_id][$bot_idx]['expire_date']);
                    file_put_contents("kilwaA.php", "<?php\nreturn " . var_export($all_bots, true) . ";\n");
                    bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ تم حذف الاشتراك بنجاح.", 'reply_markup' => json_encode(['inline_keyboard' => [[['text' => 'رجوع', 'callback_data' => 'manage_subs']]]])]);
                }
            } else {
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ البوت غير موجود في الصانع."]);
            }
        }
    }

    
    if (strpos($data, "set_duration|") === 0) {
        $months = explode("|", $data)[1];
        $temp = json_decode(file_get_contents("temp_sub.json"), true);
        
        if ($temp) {
            $all_bots = include("kilwaA.php");
            $start_date = date("Y-m-d");
            $end_date = date("Y-m-d", strtotime("+$months months"));
            
            $all_bots[$temp['owner']][$temp['idx']]['is_paid'] = true;
            $all_bots[$temp['owner']][$temp['idx']]['expire_date'] = $end_date;
            /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
            file_put_contents("kilwaA.php", "<?php\nreturn " . var_export($all_bots, true) . ";\n");
            unlink("temp_sub.json");

            bot('editMessageText', [
                'chat_id' => $chat_id, 
                'message_id' => $message_id, 
                'text' => "✅ *تم التفعيل بنجاح*", 
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode(['inline_keyboard' => [[['text' => '🔙 رجوع', 'callback_data' => 'manage_subs']]]])
            ]);
        }
    }

} 

