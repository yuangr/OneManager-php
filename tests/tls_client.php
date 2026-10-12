<?php
// Load the real shared request functions without booting a cloud deployment.
$tokens = token_get_all(file_get_contents(__DIR__ . '/../common.php'));
$allowed = ['curl', 'no_return_curl'];
for ($i = 0; $i < count($tokens); $i++) {
    if (!is_array($tokens[$i]) || $tokens[$i][0] !== T_FUNCTION) continue;
    $name = null;
    for ($j = $i + 1; $j < count($tokens); $j++) {
        if (is_array($tokens[$j]) && $tokens[$j][0] === T_STRING) { $name = $tokens[$j][1]; break; }
        if ($tokens[$j] === '(') break;
    }
    if (!in_array($name, $allowed, true)) continue;
    $source = ''; $depth = 0; $started = false;
    for ($j = $i; $j < count($tokens); $j++) {
        $token = $tokens[$j];
        $source .= is_array($token) ? $token[1] : $token;
        if ($token === '{') { $depth++; $started = true; }
        if ($token === '}') { $depth--; if ($started && $depth === 0) break; }
    }
    eval($source);
}
$response = $argv[1]('GET', $argv[2], '');
$expected = $argv[3] === 'success';
if ($expected) {
    if ($response['stat'] !== 200 || $response['body'] !== 'fixture-ok') exit(1);
} else {
    if ($response['stat'] !== 0 || $response['body'] !== false) exit(1);
}
