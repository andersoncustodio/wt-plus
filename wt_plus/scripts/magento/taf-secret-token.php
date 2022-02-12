<?php

use Magento\Framework\App\Bootstrap;

$username = $argv[1];
$magento_path = $argv[2] ?? '.';

require $magento_path . '/app/bootstrap.php';

$bootstrap = Bootstrap::create(BP, $_SERVER);
$objectManager = $bootstrap->getObjectManager();
$crypt = $objectManager->get('Magento\Framework\Encryption\EncryptorInterfaceFactory')->create();
$tfaUserConfigCollection = $objectManager->get('Magento\TwoFactorAuth\Model\ResourceModel\UserConfig\Collection');
$userCollection = $objectManager->get('Magento\User\Model\ResourceModel\User\Collection');

$user = $userCollection->getItemByColumnValue('username', $username);
$tfaUserConfig = $tfaUserConfigCollection->getItemByColumnValue('user_id', $user->getId());

$token = $crypt->decrypt($tfaUserConfig->getEncodedConfig());
$token = json_decode($token);

echo $crypt->decrypt($token->google->secret);
