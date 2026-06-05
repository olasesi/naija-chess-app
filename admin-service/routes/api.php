<?php
use App\Http\Controllers\Api\AdminController;
use App\Http\Middleware\AdminMiddleware;
use App\Http\Middleware\GatewayJwtAuth;
use Illuminate\Support\Facades\Route;

Route::prefix('admin')->middleware([GatewayJwtAuth::class, AdminMiddleware::class])->group(function () {
    Route::get('dashboard', [AdminController::class, 'dashboard']);
    Route::get('audit-log', [AdminController::class, 'auditLog']);
    Route::get('settings', [AdminController::class, 'settings']);
    Route::put('settings', [AdminController::class, 'updateSettings']);
    Route::get('reported-content', [AdminController::class, 'reportedContent']);
    Route::post('reported-content', [AdminController::class, 'createReport']);
    Route::put('reported-content/{id}', [AdminController::class, 'moderateReport']);
});
