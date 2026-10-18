<?php


// =========== إعدادات عامة ==============
ob_start();

// ضع آيدي الأدمن هنا
$admin_id = '8629412895';

// ضع توكن البوت الخاص بك
$API_KEY  = '8804551025:AAHV_zYzX_TsFQiBwNaOZVMefL7TMgZDCm4';
define('API_KEY', $API_KEY);


$storage_dir       = '@S_P_P1/yuo/kilwa/';
$users_file        = $storage_dir . 'users.json';         
$transactions_file = $storage_dir . 'transactions.json';
$referrals_file    = $storage_dir . 'referrals.json';     
$states_dir        = $storage_dir . 'states/';            
if (!is_dir($storage_dir)) {
    mkdir($storage_dir, 0777, true);
}
if (!is_dir($states_dir)) {
    mkdir($states_dir, 0777, true);
}
if (!file_exists($users_file)) {
    file_put_contents($users_file, json_encode([]));
}
if (!file_exists($transactions_file)) {
    file_put_contents($transactions_file, json_encode([]));
}
if (!file_exists($referrals_file)) {
    file_put_contents($referrals_file, json_encode([]));
}

// =========== دوال أساسية ==============
function bot($method, $datas = [])
{
    $url = "https://api.telegram.org/bot" . API_KEY . "/" . $method;
    $ch  = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    if (!empty($datas)) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($datas));
    }
    $res = curl_exec($ch);
    if (curl_errno($ch)) {
        echo "cURL Error: " . curl_error($ch);
        curl_close($ch);
        return null;
    }
    curl_close($ch);
    return json_decode($res, true);
}


function rand_text()
{
    $abc = array_merge(range('a','z'), range('0','9'));
    $text = '';
    for ($i=0; $i<10; $i++){
        $text .= $abc[array_rand($abc)];
    }
    return $text;
}


function getUser($user_id)
{
    global $users_file;
    $users = json_decode(file_get_contents($users_file), true);
    if (!isset($users[$user_id])) {
        $users[$user_id] = [
            'balance'              => 0,  
            'stars'                => 0,  
            'invited_by'           => null,
            'invited_count'        => 0,
            'earned_from_ref'      => 0,
            'payments_count'       => 0, 
            'factory_sub'          => false,
            'factory_expire'       => 0,           
            'vip_sub'              => false,
            'vip_expire'           => 0,
            'last_purchase_time'   => 0,
            'last_purchase_amount' => 0
        ];
        file_put_contents($users_file, json_encode($users));
    }
    return $users[$user_id];
}


function saveUser($user_id, $data)
{
    global $users_file;
    $users = json_decode(file_get_contents($users_file), true);
    $users[$user_id] = $data;
    file_put_contents($users_file, json_encode($users));
}


function setReferral($user_id, $ref_id)
{
    global $referrals_file;
    if ($user_id == $ref_id) {
        return;
    }
    $refs = json_decode(file_get_contents($referrals_file), true);
    if (!isset($refs[$user_id])) {
        $refs[$user_id] = $ref_id;
        file_put_contents($referrals_file, json_encode($refs));


        $refUserData = getUser($ref_id);
        $refUserData['invited_count'] = $refUserData['invited_count'] + 1;
        saveUser($ref_id, $refUserData);
    }
}
function getReferral($user_id)
{
    global $referrals_file;
    $refs = json_decode(file_get_contents($referrals_file), true);
    return $refs[$user_id] ?? null;
}


function setUserState($user_id, $stateData)
{
    global $states_dir;
    file_put_contents($states_dir."state_$user_id.json", json_encode($stateData));
}
function getUserState($user_id)
{
    global $states_dir;
    $file = $states_dir."state_$user_id.json";
    if (!file_exists($file)) {
        return ['step' => null];
    }
    return json_decode(file_get_contents($file), true);
}
function clearUserState($user_id)
{
    global $states_dir;
    $file = $states_dir."state_$user_id.json";
    if (file_exists($file)) {
        unlink($file);
    }
}


function addTransaction($user_id, $method, $amount, $operation_id='', $username='')
{
    global $transactions_file;
    $transactions = json_decode(file_get_contents($transactions_file), true);
    $tid = rand_text();
    $transactions[$tid] = [
        'user_id'      => $user_id,
        'method'       => $method,  // Payeer, Binance, VodafoneCash, TelegramStars, ...
        'amount'       => $amount,
        'operation_id' => $operation_id,
        'username'     => $username,
        'status'       => 'pending',
        'time'         => time()
    ];
    file_put_contents($transactions_file, json_encode($transactions));
    return $tid;
}
function getTransaction($tid)
{
    global $transactions_file;
    $transactions = json_decode(file_get_contents($transactions_file), true);
    return $transactions[$tid] ?? null;
}
function saveTransaction($tid, $newData)
{
    global $transactions_file;
    $transactions = json_decode(file_get_contents($transactions_file), true);
    if (isset($transactions[$tid])) {
        foreach($newData as $k=>$v) {
            $transactions[$tid][$k] = $v;
        }
        file_put_contents($transactions_file, json_encode($transactions));
    }
}

// =========== استقبال التحديثات من تيليجرام ============
$update = json_decode(file_get_contents("php://input"));

/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
if (isset($update->message)) {
    $message  = $update->message;
    $chat_id  = $message->chat->id;
    $text     = $message->text ?? '';
    $user_id  = $message->from->id;
    $name     = $message->from->first_name ?? '';
    $username = $message->from->username ?? '';

    // فحص /start مع بارامتر الدعوة
    if (preg_match('/^\/start (.*)/', $text, $match)) {
        $refParam = $match[1];
        if (strpos($refParam, 'ref=') !== false) {
            $ref_id = str_replace('ref=', '', $refParam);
            setReferral($user_id, $ref_id);
        }
    }

    $userData = getUser($user_id);
    $balance  = $userData['balance'];

    // ===== أمر /start =====
    if ($text == '/start' || strpos($text, '/start') === 0) {
        // نص رسالة الاستارت
        $welcome_text = "• مرحبا بك في بوت اشتراكات مصنع دعمكم 📮\n".
                        "~~~~~~~~~~~~\n".
                        "• يمكنك الاشتراك في الصانع أو جعل بوتك مدفوع من هنا 🗑\n".
                        "- المصنع :  @vvbcs5  🌴\n\n".
                        "• رصيدك : {$balance} USDT 💰\n".
                        "• عدد المدعوين: {$userData['invited_count']} 👫";

        // ترتيب الأزرار بحيث تكون في شكل جدول (4 أسطر × عمودين):
$reply_markup = [
    'inline_keyboard' => [
        [['text' => 'تحويل رصيد ♻️', 'callback_data' => 'transfer_balance']],
        [['text' => 'ايداع رصيد ❇️', 'callback_data' => 'deposit_balance'], ['text' => 'الاحصائيات 🛍️', 'callback_data' => 'stats']], // تم تبادل أماكن الأزرار
        [['text' => 'استرداد الاشتراك 📮', 'callback_data' => 'refund'], ['text' => 'دعوه الاصدقاء 💫', 'callback_data' => 'invite_friends']],
        [['text' => 'الاشتراكات 🗒', 'callback_data' => 'subscriptions'], ['text' => 'اشتراك المصنع 📤 ', 'callback_data' => 'factory_sub']],
        [['text' => 'نظام اشترك VIP 〽️', 'callback_data' => 'vip_sub_info']],
    ]
];
        bot('sendMessage', [
            'chat_id'    => $chat_id,
            'text'       => $welcome_text,
            'parse_mode' => 'HTML',
            'reply_markup' => json_encode($reply_markup)
        ]);
        clearUserState($user_id);
        exit;
    }

    // معالجة خطوات state
    $stateData = getUserState($user_id);
    $step      = $stateData['step'] ?? null;

    // 1) تحويل رصيد ♻️ -> الخطوة 1: انتظار ID المستقبل
    if ($step == 'waiting_transfer_address') {
        $stateData['transfer_address'] = trim($text);
        $stateData['step'] = 'waiting_transfer_amount';
        setUserState($user_id, $stateData);

        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text'    => "حسناً، الآن أدخل المبلغ الذي تريد تحويله:"
        ]);
        exit;
    }
    // 1) تحويل رصيد ♻️ -> الخطوة 2: انتظار المبلغ
    if ($step == 'waiting_transfer_amount') {
        $amount = floatval($text);
        if ($amount <= 0) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text'    => "المبلغ غير صالح، حاول مرة أخرى."
            ]);
            exit;
        }
        if ($userData['balance'] < $amount) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text'    => "رصيدك الحالي غير كافٍ لإتمام التحويل. الرصيد: {$userData['balance']} USDT"
            ]);
            clearUserState($user_id);
            exit;
        }
        // خصم المبلغ من رصيد المرسل
        $userData['balance'] -= $amount;
        saveUser($user_id, $userData);

        // الحصول على ID المستقبل
        $target_id = $stateData['transfer_address'];

        // إضافة المبلغ لرصيد المستقبل
        $targetUserData = getUser($target_id);
        $targetUserData['balance'] += $amount;
        saveUser($target_id, $targetUserData);

        clearUserState($user_id);

        // إشعار المرسل
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text'    => "تم تحويل {$amount} USDT إلى المستخدم بالمعرف: {$target_id}.\nرصيدك الحالي: {$userData['balance']} USDT"
        ]);

        // إشعار المستقبل
        bot('sendMessage', [
            'chat_id' => $target_id,
            'text'    => "لقد تلقيت تحويلاً بقيمة {$amount} USDT من المستخدم (ID: {$user_id}).\nرصيدك الحالي: {$targetUserData['balance']} USDT"
        ]);
        exit;
    }

    // خطوات الدفع اليدوي (Payeer/Binance/Vodafone) -> بعد الضغط على تم الدفع
    if ($step == 'wait_deposit_username') {
        $stateData['username'] = $text;
        $stateData['step'] = 'wait_deposit_amount';
        setUserState($user_id, $stateData);

        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text'    => "أرسل المبلغ الذي قمت بتحويله:"
        ]);
        exit;
    }
    else if ($step == 'wait_deposit_amount') {
        $amount = floatval($text);
        if ($amount <= 0) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text'    => "المبلغ غير صالح، أعد إدخاله:"
            ]);
            exit;
        }
        $stateData['amount'] = $amount;
        $stateData['step']   = 'wait_deposit_operation_id';
        setUserState($user_id, $stateData);

        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text'    => "أرسل رقم العملية أو أي معرّف يؤكد الدفع:"
        ]);
        exit;
    }
    /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
    else if ($step == 'wait_deposit_operation_id') {
        $operation_id = trim($text);
        if (strlen($operation_id) < 2) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text'    => "رقم العملية غير صالح، أعد إدخاله:"
            ]);
            exit;
        }
        $tid = addTransaction(
            $user_id,
            $stateData['deposit_method'],
            $stateData['amount'],
            $operation_id,
            $stateData['username']
        );
        // إشعار المستخدم
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text'    => "تم طلب الدفع بنجاح!\nانتظر إشعاراً من الإدارة بعد المراجعة."
        ]);

        // إشعار الأدمن
        $msg = "🚀 طلب دفع جديد: ".$stateData['deposit_method']."\n\n".
               "👤 المستخدم: $user_id\n".
               "🔸 يوزر: @".$stateData['username']."\n".
               "💵 المبلغ: ".$stateData['amount']."\n".
               "📞 رقم العملية: $operation_id\n".
               "🆔 آيدي المستخدم: $user_id\n\n".
               "هل توافق على العملية؟";
        $reply_markup = [
            'inline_keyboard' => [
                [
                    ['text'=>'الموافقة ✅','callback_data'=>"approve_$tid"],
                    ['text'=>'رفض ❌','callback_data'=>"reject_$tid"]
                ]
            ]
        ];
        bot('sendMessage', [
            'chat_id' => $admin_id,
            'text'    => $msg,
            'reply_markup' => json_encode($reply_markup)
        ]);

        clearUserState($user_id);
        exit;
    }

    // ---------- VIP عبر نجوم تيليجرام (Telegram Invoice) ----------
    if ($step == 'waiting_tgstars_amount') {
        $amount = floatval($text);
        if ($amount <= 0) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text'    => "المبلغ غير صالح. أدخل رقم بالدولار:"
            ]);
            exit;
        }
        // إعداد الفاتورة
        $prices = [
            [
                'label'  => 'نجوم تليجرام',
                'amount' => intval($amount * 100) // إذا currency=USD أو XTR بنفس الأسلوب
            ]
        ];

        // نخزن هذه المعلومات في state
        $stateData['invoice_amount'] = $amount;
        $stateData['step'] = 'waiting_tgstars_invoice';
        setUserState($user_id, $stateData);

        // إرسال الفاتورة عبر sendInvoice
        bot('sendInvoice', [
            'chat_id'         => $chat_id,
            'title'           => "شحن نجوم تليجرام",
            'description'     => "– لتاكيد الايداع قم بالضغط علي دفع 🌐",
            'payload'         => rand_text(),
            'provider_token'  => 'PROVIDER_TOKEN_HERE', // ضع التوكن الصحيح
            'start_parameter' => 'AutoCharge',
            'currency'        => 'XTR',  // أو "USD" لو أردت
            'prices'          => json_encode($prices)
        ]);

        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text'    => ""
        ]);
        exit;
    }
}

/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
if (isset($update->callback_query)) {
    $callback_query = $update->callback_query;
    $data    = $callback_query->data;
    $cq_id   = $callback_query->id;
    $chat_id = $callback_query->message->chat->id;
    $msg_id  = $callback_query->message->message_id;
    $user_id = $callback_query->from->id;

    $userData = getUser($user_id);
    $balance  = $userData['balance'];
    $username = isset($update->callback_query->from->username) ? $update->callback_query->from->username : '';

    // زر الرجوع العام
    if ($data == 'back_to_menu') {
        $welcome_text = "• مرحبا بك في بوت اشتراكات مصنع دعمكم 📮\n".
                        "~~~~~~~~~~~~\n".
                        "• يمكنك الاشتراك في الصانع أو جعل بوتك مدفوع من هنا 🗑\n".
                        "- المصنع :  @nkrmbot  🌴\n\n".
                        "• رصيدك : {$balance} USDT 💰\n".
                        "• عدد المدعوين: {$userData['invited_count']} 👫";

$reply_markup = [
    'inline_keyboard' => [
        [['text' => 'تحويل رصيد ♻️', 'callback_data' => 'transfer_balance']],
        [['text' => 'ايداع رصيد ❇️', 'callback_data' => 'deposit_balance'], ['text' => 'الاحصائيات 🛍️', 'callback_data' => 'stats']], // تم تبادل أماكن الأزرار
        [['text' => 'استرداد الاشتراك 📮', 'callback_data' => 'refund'], ['text' => 'دعوه الاصدقاء 💫', 'callback_data' => 'invite_friends']],
        [['text' => 'الاشتراكات 🗒', 'callback_data' => 'subscriptions'], ['text' => 'اشتراك المصنع 📤 ', 'callback_data' => 'factory_sub']],
        [['text' => 'نظام اشترك VIP 〽️', 'callback_data' => 'vip_sub_info']],
    ]
];     
  bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $welcome_text,
            'reply_markup'=> json_encode($reply_markup)
        ]);
        exit;
    }

    /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
    if ($data == 'transfer_balance') {
        $stateData = ['step' => 'waiting_transfer_address'];
        setUserState($user_id, $stateData);

        $reply_markup = [
            'inline_keyboard' => [
                [['text' => 'رجوع', 'callback_data' => 'back_to_menu']]
            ]
        ];
        bot('editMessageText', [
            'chat_id'      => $chat_id,
            'message_id'   => $msg_id,
            'text'         => "• ارسل عنوان الشخص 📮",
            'reply_markup' => json_encode($reply_markup)
        ]);
        exit;
    }

    // =========== (2) ايداع رصيد ❇️ ===========
    if ($data == 'deposit_balance') {
        $text = "• يمكنك شحن حسابك عن طريق 💎\n".
                "~~~~~~~~~\n".
                "1- شحن بايير = 1$\n".
                "2- شحن بينانس = 1$\n".
                "3- نجوم تلجرام = 1\$ مقابل 100 نجمة (تلقائي)\n".
                "4- فودافون كاش = 50 جنيه\n".
                "~~~~~~~~~\n".
                "• هذه هي طرق الايداع المتوفره لدينا ⚙️\n\n".
                "• هذا العنوان يخص الاستلام فقط 📮\n".
                "----------------------------\n".
                "– باقي طرق الايداع من هنا @TiTqq\n\n".
                "اختر الطريقة المناسبة:";
        $reply_markup = [
            'inline_keyboard' => [
                [
                    ['text' => 'بايير',       'callback_data' => 'dep_payeer'],
                    ['text' => 'بينانس',      'callback_data' => 'dep_binance']
                ],
                [
                    ['text' => 'نجوم تلجرام','callback_data' => 'dep_telegram_stars'],
                    ['text' => 'فودافون كاش','callback_data' => 'dep_vodafone']
                ],
                [
                    ['text' => 'رجوع', 'callback_data' => 'back_to_menu']
                ]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'reply_markup' => json_encode($reply_markup)
        ]);
        exit;
    }

    /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
    if ($data == 'dep_binance') {
        $text = "تفاصيل الدفع عبر Binance:\n\n".
                "1. قم بتحويل المبلغ إلى المعرف التالي:\n".
                "`987333981`\n\n".
                "2. اضغط '✅ تم الدفع' بعد التحويل.\n";
        $reply_markup = [
            'inline_keyboard' => [
                [['text'=>'✅ تم الدفع','callback_data'=>'binance_paid']],
                [['text'=>'رجوع','callback_data'=>'deposit_balance']]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode($reply_markup)
        ]);
        exit;
    }
    if ($data == 'binance_paid') {
        $stateData = [
            'step'           => 'wait_deposit_username',
            'deposit_method' => 'Binance'
        ];
        setUserState($user_id, $stateData);

        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => "أرسل اسم المستخدم الخاص بك (UserName) أو أي معرّف تريده:"
        ]);
        exit;
    }

    // ---- 2-2) بايير ----
    if ($data == 'dep_payeer') {
        $text = "تفاصيل الدفع عبر Payeer:\n\n".
                "1. قم بتحويل المبلغ إلى الحساب التالي: `Pxxxxxxx`\n\n".
                "2. اضغط '✅ تم الدفع' بعد التحويل.\n";
        $reply_markup = [
            'inline_keyboard' => [
                [['text'=>'✅ تم الدفع','callback_data'=>'payeer_paid']],
                [['text'=>'رجوع','callback_data'=>'deposit_balance']]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode($reply_markup)
        ]);
        exit;
    }
    if ($data == 'payeer_paid') {
        $stateData = [
            'step'           => 'wait_deposit_username',
            'deposit_method' => 'Payeer'
        ];
        setUserState($user_id, $stateData);

        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => "أرسل اسم المستخدم الخاص بك (UserName) في Payeer أو تيليجرام:"
        ]);
        exit;
    }

    /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
    if ($data == 'dep_vodafone') {
        $text = "تفاصيل الدفع عبر فودافون كاش:\n\n".
                "1. قم بتحويل 50 جنيه إلى الرقم: `010xxxxxxxx`\n\n".
                "2. اضغط '✅ تم الدفع' بعد التحويل.\n";
        $reply_markup = [
            'inline_keyboard' => [
                [['text'=>'✅ تم الدفع','callback_data'=>'vodafone_paid']],
                [['text'=>'رجوع','callback_data'=>'deposit_balance']]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode($reply_markup)
        ]);
        exit;
    }
    if ($data == 'vodafone_paid') {
        $stateData = [
            'step'           => 'wait_deposit_username',
            'deposit_method' => 'VodafoneCash'
        ];
        setUserState($user_id, $stateData);

        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => "أرسل اسمك أو رقمك الذي أرسلت منه:"
        ]);
        exit;
    }

    // ---- 2-4) نجوم تلجرام (تلقائي) ----
    if ($data == 'dep_telegram_stars') {
        $stateData = [
            'step' => 'waiting_tgstars_amount'
        ];
        setUserState($user_id, $stateData);

        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => "أدخل المبلغ بالدولار الذي تريد شحنه (كل 1\$ = 100 نجمة):",
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => 'رجوع', 'callback_data' => 'deposit_balance']]
                ]
            ])
        ]);
        exit;
    }
/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
    if ($data == 'stats') {
        // عرض قائمة بطرق الدفع للاطلاع على تاريخ المعاملات
        $text = "اختر وسيلة الدفع لعرض إحصائيات معاملاتك:";
        $reply_markup = [
            'inline_keyboard' => [
                [
                    ['text'=>'Payeer','callback_data'=>'stats_payeer'],
                    ['text'=>'Binance','callback_data'=>'stats_binance']
                ],
                [
                    ['text'=>'VodafoneCash','callback_data'=>'stats_vodafone'],
                    ['text'=>'نجوم تلجرام','callback_data'=>'stats_telegramstars']
                ],
                [
                    ['text'=>'عرض الكل','callback_data'=>'stats_all']
                ],
                [
                    ['text'=>'رجوع','callback_data'=>'back_to_menu']
                ]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'reply_markup'=> json_encode($reply_markup)
        ]);
        exit;
    }

    function showUserTransactions($chat_id, $msg_id, $user_id, $methodFilter=null) {
        global $transactions_file;
        $transactions = json_decode(file_get_contents($transactions_file), true);
        $lines = [];
        foreach($transactions as $tid=>$t) {
            if ($t['user_id'] == $user_id) {
                if ($methodFilter && $t['method'] != $methodFilter) {
                    continue;
                }
                $dateStr = date('Y-m-d H:i', $t['time']);
                $status  = $t['status'];
                $amount  = $t['amount'];
                $opid    = $t['operation_id'];
                $lines[] = "معاملة: <b>$tid</b>\n".
                           "التاريخ: $dateStr\n".
                           "المبلغ: $amount\n".
                           "رقم العملية: $opid\n".
                           "الحالة: $status\n".
                           "------------";
            }
        }
        if (count($lines)==0) {
            $txt = "لا توجد معاملات";
        } else {
            $txt = implode("\n",$lines);
        }
        $reply_markup = [
            'inline_keyboard' => [
                [['text'=>'رجوع','callback_data'=>'stats']]
            ]
        ];
        bot('editMessageText', [
            'chat_id'=>$chat_id,
            'message_id'=>$msg_id,
            'text'=>$txt,
            'parse_mode'=>'HTML',
            'reply_markup'=>json_encode($reply_markup)
        ]);
    }

    if ($data == 'stats_payeer') {
        showUserTransactions($chat_id, $msg_id, $user_id, 'Payeer');
        exit;
    }
    if ($data == 'stats_binance') {
        showUserTransactions($chat_id, $msg_id, $user_id, 'Binance');
        exit;
    }
    if ($data == 'stats_vodafone') {
        showUserTransactions($chat_id, $msg_id, $user_id, 'VodafoneCash');
        exit;
    }
    if ($data == 'stats_telegramstars') {
        showUserTransactions($chat_id, $msg_id, $user_id, 'TelegramStars');
        exit;
    }
    if ($data == 'stats_all') {
        showUserTransactions($chat_id, $msg_id, $user_id, null);
        exit;
    }

    // =========== (4) دعوه الاصدقاء 💫 ===========
    if ($data == 'invite_friends') {
        $botUser = bot('getMe');
        $botUsername = $botUser['result']['username'] ?? 'MyBot';

        $invited_count= $userData['invited_count'];
        $earned       = $userData['earned_from_ref'];

        $inviteLink   = "https://t.me/{$botUsername}?start=ref={$user_id}";

        $msg = "• دعوه الاصدقاء وربح الرصيد 🌟\n".
               "~~~~~~~~~~~~\n".
               "• رابط الدعوة الخاص بك:\n".
               "$inviteLink\n\n".
               "• عدد الأصدقاء المدعوين: $invited_count 👫\n".
               "• إجمالي الأرباح: $earned \$ 💰\n\n".
               "- شارك رابطك مع أصدقائك واربح 10% من أرباحهم عندما يقومون بالشحن!  🎁";

        $reply_markup = [
            'inline_keyboard' => [
                [['text'=>'رجوع','callback_data'=>'back_to_menu']]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $msg,
            'reply_markup'=> json_encode($reply_markup)
        ]);
        exit;
    }

    // =========== (5) اشتراك المصنع (تفعيل بوت مدفوع) 📤 ===========
    if ($data == 'factory_sub') {
        // عرض مدد الاشتراك والأسعار
        $text = "اختر مدة الاشتراك لتفعيل بوتك كـ (مدفوع/VIP):\n\n".
                "1 شهر = 1\$\n".
                "3 شهور = 3\$\n".
                "6 شهور = 5\$\n".
                "12 شهر = 9\$\n";
        $reply_markup = [
            'inline_keyboard' => [
                [
                    ['text'=>'1 شهر (1$)','callback_data'=>'select_duration|1|1'],
                    ['text'=>'3 شهور (3$)','callback_data'=>'select_duration|3|3']
                ],
                [
                    ['text'=>'6 شهور (5$)','callback_data'=>'select_duration|6|5'],
                    ['text'=>'12 شهر (9$)','callback_data'=>'select_duration|12|9']
                ],
                [
                    ['text'=>'رجوع','callback_data'=>'back_to_menu']
                ]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'reply_markup'=> json_encode($reply_markup)
        ]);
        exit;
    }

    // خطوة 2: بعد اختيار المدة -> عرض البوتات
        // داخل شرط select_duration|
    if (strpos($data, 'select_duration|') === 0) {
        $ex = explode('|', $data);
        $months = $ex[1];
        $price  = $ex[2];

        if (!file_exists("kilwaA.php")) {
            bot('answerCallbackQuery', ['callback_query_id' => $cq_id, 'text' => "⚠️ ملف البوتات غير موجود!", 'show_alert' => true]);
            exit;
        }

        $all_bots = include("kilwaA.php");
        $user_bots = $all_bots[$user_id] ?? [];

        // --- التعديل هنا: رسالة عدم وجود بوتات ---
        if (empty($user_bots)) {
            bot('editMessageText', [
                'chat_id' => $chat_id,
                'message_id' => $msg_id,
                'text' => "لا يوجد بوتات عندك الان يرجا صنع بوت من خلال الصانع",
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
        /*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
                        [['text' => 'الذهاب للصانع 🤖', 'url' => 'https://t.me/YOUR_MAKER_BOT']], 
                        [['text' => 'رجوع', 'callback_data' => 'factory_sub']]
                    ]
                ])
            ]);
            exit;
        }
        // -----------------------------------------

        // باقي الكود كما هو (عرض البوتات)...
        $keyboard = [];
        foreach ($user_bots as $idx => $bot) {
            $keyboard[] = [['text' => $bot['bot_username'], 'callback_data' => "activate_bot|$idx|$price|$months"]];
        }
        $keyboard[] = [['text' => '🔙 رجوع', 'callback_data' => 'factory_sub']];

        bot('editMessageText', [
            'chat_id' => $chat_id,
            'message_id' => $msg_id,
            'text' => "🤖 *اختر البوت الذي تريد تفعيل الاشتراك له:*\n\n💰 السعر: $price \$\n📅 المدة: $months شهر",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => $keyboard])
        ]);
        exit;
    }

    // خطوة 3: التنفيذ (الخصم والتفعيل الفوري)
    if (strpos($data, 'activate_bot|') === 0) {
        $ex = explode('|', $data);
        $bot_idx = $ex[1]; // ترتيب البوت
        $price   = $ex[2];
        $months  = $ex[3];

        // ★★★ ضع توكن البوت الصانع هنا لكي يرسل الإشعار ★★★
        $maker_token = "8492778130:AAF4YmJvvJQ7LWeCxHlU3-8QyiOEezQlFUk"; 
        // مثال: $maker_token = "123456789:ABCdef...";

        // 1. التحقق من وجود البوت
        if (!file_exists("kilwaA.php")) {
            bot('answerCallbackQuery', ['callback_query_id' => $cq_id, 'text' => "❌ خطأ: ملف البيانات مفقود.", 'show_alert' => true]);
            exit;
        }
        $all_bots = include("kilwaA.php");

        if (!isset($all_bots[$user_id][$bot_idx])) {
            bot('answerCallbackQuery', ['callback_query_id' => $cq_id, 'text' => "❌ حدث خطأ، البوت غير موجود.", 'show_alert' => true]);
            exit;
        }

        // 2. التحقق: هل هو مشترك بالفعل والاشتراك ساري؟
        $current_bot_data = $all_bots[$user_id][$bot_idx];
        if (isset($current_bot_data['is_paid']) && $current_bot_data['is_paid'] == true) {
            // نتحقق من التاريخ
            if (isset($current_bot_data['expire_date']) && strtotime($current_bot_data['expire_date']) > time()) {
                // الاشتراك لا يزال سارياً
                bot('answerCallbackQuery', [
                    'callback_query_id' => $cq_id, 
                    'text' => "⚠️ عذراً، هذا البوت مشترك بالفعل واشتراكه ساري حتى " . $current_bot_data['expire_date'], 
                    'show_alert' => true
                ]);
                exit; // إيقاف العملية
            }
        }

        // 3. التحقق من الرصيد
        if ($userData['balance'] < $price) {
            bot('answerCallbackQuery', ['callback_query_id' => $cq_id, 'text' => "❌ رصيدك غير كافٍ! (تحتاج $price$)", 'show_alert' => true]);
            exit;
        }

        // 4. خصم الرصيد
        $userData['balance'] -= $price;
        $userData['last_purchase_time'] = time();
        $userData['last_purchase_amount'] = $price;
        saveUser($user_id, $userData);

        // 5. تفعيل الاشتراك (تحديث الملف)
        // إذا كان منتهي يبدأ من اليوم، لو لم يكن له تاريخ يبدأ من اليوم
        $current_expire = time(); 
        
        $new_expire = date("Y-m-d", strtotime("+$months months", $current_expire));
        
        $all_bots[$user_id][$bot_idx]['is_paid'] = true;
        $all_bots[$user_id][$bot_idx]['expire_date'] = $new_expire;
        
        file_put_contents("kilwaA.php", "<?php\nreturn " . var_export($all_bots, true) . ";\n");

        // 6. رسالة النجاح (في بوت الدفع)
        bot('editMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $msg_id, 
            'text' => "✅ *تم تفعيل الاشتراك بنجاح!* 🎉\n\n" .
                      "🤖 البوت: `" . $all_bots[$user_id][$bot_idx]['bot_username'] . "`\n" .
                      "📅 ينتهي في: `$new_expire`\n\n" .
                      "تم إرسال تفاصيل الفاتورة إليك في الصانع 📨", 
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['inline_keyboard' => [[['text' => 'القائمة الرئيسية', 'callback_data' => 'back_to_menu']]]])
        ]);

        // 7. إرسال إشعار في (البوت الصانع)
        $msg_maker = "✅ *تمت عملية اشتراك مدفوع بنجاح*\n\n" .
                     "🤖 *البوت:* @" . str_replace('@', '', $all_bots[$user_id][$bot_idx]['bot_username']) . "\n" .
                     "📅 *تاريخ البدء:* " . date('Y-m-d') . "\n" .
                     "🛑 *تاريخ الانتهاء:* $new_expire\n" .
                     "💰 *القيمة:* $price $\n\n" .
                     "شكراً لاستخدامك خدماتنا المدفوعة 🌹";
                     
        // نستخدم file_get_contents لإرسال الرسالة بتوكن الصانع
        if ($maker_token != "8492778130:AAF4YmJvvJQ7LWeCxHlU3-8QyiOEezQlFUk") {
            $url = "https://api.telegram.org/bot$maker_token/sendMessage?chat_id=$chat_id&text=" . urlencode($msg_maker) . "&parse_mode=Markdown";
            file_get_contents($url);
        }
        
        // إشعار للأدمن (بوت الدفع)
        bot('sendMessage', [
            'chat_id' => $admin_id,
            'text' => "💰 *عملية اشتراك جديدة*\n👤 المستخدم: $user_id\n🤖 البوت: ".$all_bots[$user_id][$bot_idx]['bot_username']."\n💵 المبلغ: $price $\n📅 المدة: $months شهر"
        ]);
        exit;
    }



    // =========== (6) زر الاشتراكات 🗒 (VIP وغيره) ===========
    // =========== (6) زر الاشتراكات 🗒 (VIP وغيره) ===========
    if ($data == 'subscriptions') {
        $text = "- يرجى تحديد نوع الاشتراك الذي تود معرفته 📝";
        $reply_markup = [
            'inline_keyboard' => [
                [
                    ['text'=>'اشتراك المصنع 📤','callback_data'=>'factory_sub'],
                    ['text'=>'تجديد اشتراك بوتاتي 🤖','callback_data'=>'renew_my_bots'] // زر جديد
                ],
                [
                    ['text'=>'اشتراك الشحن (VIP)','callback_data'=>'vip_sub_info']
                ],
                [
                    ['text'=>'رجوع','callback_data'=>'back_to_menu']
                ]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'reply_markup'=> json_encode($reply_markup)
        ]);
        exit;
    }


    if ($data == 'vip_sub_info') {
        if ($userData['vip_sub'] && $userData['vip_expire'] > time()) {
            $remaining = $userData['vip_expire'] - time();
            $days = ceil($remaining / 86400);
            $msg = "لديك اشتراك VIP حالي.\nينتهي خلال: {$days} يوم تقريباً.";
            bot('editMessageText', [
                'chat_id'    => $chat_id,
                'message_id' => $msg_id,
                'text'       => $msg,
                'reply_markup'=> json_encode([
                    'inline_keyboard' => [
                        [['text'=>'رجوع','callback_data'=>'back_to_menu']]
                    ]
                ])
            ]);
        } else {
            $msg = "🔹 ليس لديك اشتراك VIP حالي.\n".
                   "~~~~~~~~~~~~\n".
                   "يمكنك الاشتراك بالنقر على الزر أدناه. 🛒";
            $reply_markup = [
                'inline_keyboard' => [
                    [['text'=>'اشترك جديد','callback_data'=>'vip_new']],
                    [['text'=>'رجوع','callback_data'=>'back_to_menu']]
                ]
            ];
            bot('editMessageText', [
                'chat_id'    => $chat_id,
                'message_id' => $msg_id,
                'text'       => $msg,
                'reply_markup'=> json_encode($reply_markup)
            ]);
        }
        exit;
    }

    if ($data == 'vip_new') {
        $text = "اختر مدة الاشتراك التي تريدها في نظام VIP 📮\n".
                "~~~~~~~~~~~~\n".
                "1 شهر = 2 USDT\n".
                "2 شهر = 4 USDT\n".
                "3 شهر = 6 USDT\n".
                "4 شهر = 8 USDT\n".
                "5 شهر = 10 USDT\n\n".
                "اشحن رصيدك أولاً إن لم يكن لديك رصيد كافٍ.";
        $reply_markup = [
    'inline_keyboard' => [
        [['text'=>'🛒 1 شهر','callback_data'=>'vip_1m'], ['text'=>'2 USDT 💸','callback_data'=>'vip_1m']],
        [['text'=>'🛒 2 أشهر','callback_data'=>'vip_2m'], ['text'=>'4 USDT 💸','callback_data'=>'vip_2m']],
        [['text'=>'🛒 3 أشهر','callback_data'=>'vip_3m'], ['text'=>'6 USDT 💸','callback_data'=>'vip_3m']],
        [['text'=>'🛒 4 أشهر','callback_data'=>'vip_4m'], ['text'=>'8 USDT 💸','callback_data'=>'vip_4m']],
        [['text'=>'🛒 5 أشهر','callback_data'=>'vip_5m'], ['text'=>'10 USDT 💸','callback_data'=>'vip_5m']],
        [['text'=>'🔙 رجوع','callback_data'=>'back_to_menu']]
    ]
];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'reply_markup'=> json_encode($reply_markup)
        ]);
        exit;
    }

    if (in_array($data, ['vip_1m','vip_2m','vip_3m','vip_4m','vip_5m'])) {
        $price_map = [
            'vip_1m' => 2,
            'vip_2m' => 4,
            'vip_3m' => 6,
            'vip_4m' => 8,
            'vip_5m' => 10
        ];
        $duration_map = [
            'vip_1m' => 30*24*3600,
            'vip_2m' => 60*24*3600,
            'vip_3m' => 90*24*3600,
            'vip_4m' => 120*24*3600,
            'vip_5m' => 150*24*3600
        ];
        $sub_price = $price_map[$data];
        $duration  = $duration_map[$data];

        if ($balance < $sub_price) {
            bot('editMessageText', [
                'chat_id'    => $chat_id,
                'message_id' => $msg_id,
                'text'       => "رصيدك الحالي غير كافٍ للاشتراك.\nالرصيد الحالي: $balance USDT.\nأعد شحن رصيدك ➕",
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [['text'=>'ايداع رصيد ❇️','callback_data'=>'deposit_balance']],
                        [['text'=>'رجوع','callback_data'=>'back_to_menu']]
                    ]
                ])
            ]);
            exit;
        }
        $userData['balance'] -= $sub_price;
        $userData['vip_sub']    = true;
        $userData['vip_expire'] = time() + $duration;

        // تخزين وقت ومبلغ آخر شراء
        $userData['last_purchase_time']   = time();
        $userData['last_purchase_amount'] = $sub_price;

        saveUser($user_id, $userData);

        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => "تم تفعيل اشتراك VIP بنجاح.\nاستمتع بخدمات VIP والمزايا الإضافية!"
        ]);

        $days = $duration / 86400;
        bot('sendMessage', [
            'chat_id' => $admin_id,
            'text' => "🚀 اشتراك VIP جديد\n\n".
                      "👤 المستخدم: $name\n".
                      "💵 المبلغ: $sub_price\n".
                      "اليوزر: @$username\n".
                      "ايدي المستخدم: $user_id\n".
                      "المدة: {$days} يوم\n".
                      "الرصيد بعد الخصم: ".$userData['balance']
        ]);
        exit;
    }

    // =========== (7) نظام VIP (VIP) ===========
    if ($data == 'vip_auto') {
        if ($userData['vip_sub'] && $userData['vip_expire'] > time()) {
            $msg = "مرحباً بك في نظام VIP (VIP)\n".
                   "لديك اشتراك VIP فعال حالياً.\n".
                   "يمكنك الاستفادة من المزايا المختلفة...";
            bot('editMessageText', [
                'chat_id'    => $chat_id,
                'message_id' => $msg_id,
                'text'       => $msg,
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [['text'=>'رجوع','callback_data'=>'back_to_menu']]
                    ]
                ])
            ]);
        } else {
            $msg = "ليس لديك اشتراك VIP.\nيرجى الاشتراك أولاً للاستفادة من نظام VIP.";
            bot('editMessageText', [
                'chat_id'    => $chat_id,
                'message_id' => $msg_id,
                'text'       => $msg,
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        [['text'=>'اشتراك VIP','callback_data'=>'vip_sub_info']],
                        [['text'=>'رجوع','callback_data'=>'back_to_menu']]
                    ]
                ])
            ]);
        }
        exit;
    }

    // =========== (8) استرداد الاشتراك 📮 ===========
    
        // =========== (9) تجديد اشتراك البوتات (زر تجديد اشتراك بوتاتي) ===========
    if ($data == 'renew_my_bots') {
        // 1. التأكد من وجود ملف البوتات
        if (!file_exists("kilwaA.php")) {
            bot('answerCallbackQuery', ['callback_query_id' => $cq_id, 'text' => "عذراً، ملف البوتات غير متوفر حالياً.", 'show_alert' => true]);
            exit;
        }
        
        $all_bots = include("kilwaA.php");
        $user_bots = $all_bots[$user_id] ?? [];

        // 2. فحص إذا كان المستخدم لا يملك بوتات
        if (empty($user_bots)) {
            bot('editMessageText', [
                'chat_id' => $chat_id, 
                'message_id' => $msg_id, 
                'text' => "لا يوجد بوتات عندك الان يرجا صنع بوت من خلال الصانع",
                'reply_markup' => json_encode([
                    'inline_keyboard' => [
                        // ⚠️ استبدل الرابط أدناه برابط بوت الصانع الخاص بك
                        [['text' => 'الذهاب للصانع 🤖', 'url' => 'https://t.me/YOUR_MAKER_BOT']],
                        [['text' => 'رجوع', 'callback_data' => 'subscriptions']]
                    ]
                ])
            ]);
            exit;
        }

        // 3. إذا كان لديه بوتات، يوجهه لاختيار المدة مباشرة
        $text = "اختر مدة التجديد لبوتك:\n\n1 شهر = 1\$\n3 شهور = 3\$\n6 شهور = 5\$\n12 شهر = 9\$\n";
        $reply_markup = [
            'inline_keyboard' => [
                [['text'=>'1 شهر (1$)','callback_data'=>'select_duration|1|1'], ['text'=>'3 شهور (3$)','callback_data'=>'select_duration|3|3']],
                [['text'=>'6 شهور (5$)','callback_data'=>'select_duration|6|5'], ['text'=>'12 شهر (9$)','callback_data'=>'select_duration|12|9']],
                [['text'=>'رجوع','callback_data'=>'subscriptions']]
            ]
        ];
        bot('editMessageText', [
            'chat_id' => $chat_id, 
            'message_id' => $msg_id, 
            'text' => $text, 
            'reply_markup' => json_encode($reply_markup)
        ]);
        exit;
    }


    if ($data == 'refund') {
        // رسالة تعريفية + زر طلب الاسترداد
        $text = "إذا واجهتك مشكلة أو لم يعجبك شيء في البوت، يمكنك طلب الاسترداد خلال 24 ساعة من الاشتراك.\n".
                "سيتم خصم 10% كعمولة استرداد.\n\n".
                "هل تريد المتابعة؟";

        $reply_markup = [
            'inline_keyboard' => [
                [
                    ['text'=>'كيد على قراري وأريد استرداد المبلغ','callback_data'=>'refund_request']
                ],
                [
                    ['text'=>'رجوع','callback_data'=>'back_to_menu']
                ]
            ]
        ];
        bot('editMessageText', [
            'chat_id'    => $chat_id,
            'message_id' => $msg_id,
            'text'       => $text,
            'reply_markup'=> json_encode($reply_markup)
        ]);
        exit;
    }
    if ($data == 'refund_request') {
        $now      = time();
        $lp_time  = isset($userData['last_purchase_time']) ? $userData['last_purchase_time'] : 0;
        $lp_amount= isset($userData['last_purchase_amount']) ? $userData['last_purchase_amount'] : 0;

        if ($lp_time == 0 || $lp_amount == 0) {
            // لم يقم بأي اشتراك قريب
            bot('answerCallbackQuery', [
                'callback_query_id' => $cq_id,
                'text' => "لا يوجد اشتراك مدفوع مؤخراً للاسترداد.",
                'show_alert' => true
            ]);
            exit;
        }

        // تحقق من المدة
        $diff = $now - $lp_time;
        if ($diff > 86400) { // 24 ساعة = 86400 ثانية
            bot('answerCallbackQuery', [
                'callback_query_id' => $cq_id,
                'text' => "عذراً، لا يمكن طلب الاسترداد بعد مرور 24 ساعة من الاشتراك.",
                'show_alert' => true
            ]);
            exit;
        }

        // ضمن 24 ساعة -> نخصم 10%
        $refund_amount = $lp_amount * 0.9; // 90% للمستخدم
        $userData['balance'] += $refund_amount;

        // يمكننا إلغاء الاشتراك (المصنع و VIP) لو أردنا
        if ($userData['factory_sub']) {
            $userData['factory_sub'] = false;
            $userData['factory_expire'] = 0;
        }
        if ($userData['vip_sub']) {
            $userData['vip_sub'] = false;
            $userData['vip_expire'] = 0;
        }

        // نظف آخر شراء حتى لا يطلب استرداد مرة أخرى
        $userData['last_purchase_time']   = 0;
        $userData['last_purchase_amount'] = 0;

        saveUser($user_id, $userData);

        // رسالة للمستخدم
bot('editMessageText', [
    'chat_id'    => $chat_id,
    'message_id' => $msg_id,
    'text'       => "تمت إعادة {$refund_amount} USDT إلى رصيدك بنجاح.\n" .
                    "رصيدك الحالي: {$userData['balance']} USDT\n\n" .
                    "تم خصم 10% كعمولة استرداد.\n\n" .
                    "نأسف لعدم رضاك، يمكنك التواصل مع الدعم للمساعدة.",
    'reply_markup' => json_encode([
        'inline_keyboard' => [
            [
                ['text' => 'تواصل مع الأدمن', 'url' => 'https://t.me/TiTqq']],
                [['text' => 'رجوع', 'callback_data' => 'back_to_menu']
            ]
        ]
    ])
]);

        // إشعار للأدمن
        bot('sendMessage', [
            'chat_id' => $admin_id,
            'text'    => "طلب استرداد من المستخدم:\n".
                         "👤 $user_id ( @$username )\n".
                         "تم رد مبلغ: $refund_amount (من أصل $lp_amount)\n".
                         "وإلغاء الاشتراك لديه."
        ]);
        exit;
    }

    // =========== موافقة/رفض الأدمن على المعاملة ===========
    if (strpos($data, 'approve_') === 0 || strpos($data, 'reject_') === 0) {
        // تحقق هل المستخدم هو الأدمن؟
        if ($user_id != $admin_id) {
            bot('answerCallbackQuery', [
                'callback_query_id' => $cq_id,
                'text' => "غير مسموح.",
                'show_alert' => true
            ]);
            exit;
        }
        $tid = explode('_', $data)[1];
        $transaction = getTransaction($tid);
        if (!$transaction) {
            bot('answerCallbackQuery', [
                'callback_query_id' => $cq_id,
                'text' => "لا توجد معاملة بهذا المعرّف!",
                'show_alert' => true
            ]);
            exit;
        }
        if ($transaction['status'] != 'pending') {
            bot('answerCallbackQuery', [
                'callback_query_id' => $cq_id,
                'text' => "تمت معالجة هذه المعاملة سابقاً.",
                'show_alert' => true
            ]);
            exit;
        }

        $t_user_id = $transaction['user_id'];
        $t_amount  = $transaction['amount'];
        $t_method  = $transaction['method'];

        if (strpos($data, 'approve_')===0) {
            // موافقة
            $uData = getUser($t_user_id);
            $uData['balance'] += $t_amount;
            $uData['payments_count'] += 1;
            saveUser($t_user_id, $uData);

            saveTransaction($tid, ['status'=>'approved']);

            // مكافأة الداعي
            $ref_id = getReferral($t_user_id);
            if ($ref_id) {
                $bonus = 0.1 * $t_amount;
                $refUser = getUser($ref_id);
                $refUser['balance'] += $bonus;
                $refUser['earned_from_ref'] += $bonus;
                saveUser($ref_id, $refUser);
            }

            // إشعار المستخدم
            bot('sendMessage', [
                'chat_id' => $t_user_id,
                'text' => "تمت الموافقة على عملية الدفع الخاصة بك ($t_amount\$). رصيدك الحالي: ".$uData['balance']
            ]);
            // تعديل رسالة الأدمن
            bot('editMessageText', [
                'chat_id'    => $chat_id,
                'message_id' => $msg_id,
                'text'       => "تمت الموافقة على معاملة $tid\nرصيد المستخدم أصبح: ".$uData['balance']
            ]);
        } else {
            // رفض
            saveTransaction($tid, ['status'=>'rejected']);
            bot('sendMessage', [
                'chat_id' => $t_user_id,
                'text' => "تم رفض عملية الدفع الخاصة بك.\nيمكنك التواصل مع الإدارة لمزيد من التفاصيل."
            ]);
            bot('editMessageText', [
                'chat_id'    => $chat_id,
                'message_id' => $msg_id,
                'text'       => "تم رفض معاملة $tid"
            ]);
        }
        exit;
    }
}

// ----------------------------------------------
// 3) التعامل مع مدفوعات تيليجرام (Invoices)
// ----------------------------------------------
if (isset($update->pre_checkout_query)) {
    $pre_checkout_query_id = $update->pre_checkout_query->id;
    // الموافقة على الفاتورة
    bot('answerPreCheckoutQuery', [
        'pre_checkout_query_id' => $pre_checkout_query_id,
        'ok' => true
    ]);
}

/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/
if (isset($update->message->successful_payment)) {
    $msg        = $update->message;
    $chat_id    = $msg->chat->id;
    $user_id    = $msg->from->id;
    $username   = $msg->from->username ?? '';
    $payment    = $msg->successful_payment;
    $total_paid = $payment->total_amount / 100; // لأننا وضعنا *100

    // إضافة النجوم (مثال: 1$ = 100 نجمة)
    $userData = getUser($user_id);
    $stars_gained = $total_paid * 100;
    $userData['stars'] += $stars_gained;
    $userData['payments_count'] += 1;
    saveUser($user_id, $userData);

    // أنشئ معاملة مباشرة approved
    $tid = addTransaction($user_id, 'TelegramStars', $total_paid, 'AutoInvoice', $username);
    saveTransaction($tid, ['status'=>'approved']);

    // مكافأة الداعي (10%)
    $ref_id = getReferral($user_id);
    if ($ref_id) {
        $bonus = 0.1 * $total_paid;
        $refUser = getUser($ref_id);
        $refUser['balance'] += $bonus;
        $refUser['earned_from_ref'] += $bonus;
        saveUser($ref_id, $refUser);
    }

    // إشعار المستخدم
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "✅ تم الدفع بنجاح عبر Telegram!\n".
                  "تم إضافة $stars_gained نجمة إلى حسابك.\n".
                  "إجمالي النجوم: ".$userData['stars']
    ]);

    // إشعار الأدمن
    bot('sendMessage', [
        'chat_id' => $admin_id,
        'text'    => "تمت عملية دفع تلقائية عبر نجوم تيليجرام\n".
                     "👤 المستخدم: $user_id\n".
                     "🔸 يوزر: @$username\n".
                     "💵 المبلغ: $total_paid \$\n".
                     "عدد النجوم المضافة: $stars_gained\n".
                     "الحالة: Approved\n".
                     "المعرف: $tid"
    ]);
}
?>

/*
--- تم تطوير هذا الملف بواسطة المطور @X_V_44 ---
--- قناة المطور: @php_72 ---
*/