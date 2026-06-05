<?php
use App\Http\Controllers\Api\ForumController;
use App\Http\Middleware\GatewayJwtAuth;
use Illuminate\Support\Facades\Route;

Route::prefix('forum')->middleware(GatewayJwtAuth::class)->group(function () {
    // Categories
    Route::get('categories', [ForumController::class, 'categories']);
    Route::post('categories', [ForumController::class, 'storeCategory']);

    // Threads
    Route::get('threads', [ForumController::class, 'threads']);
    Route::post('threads', [ForumController::class, 'storeThread']);
    Route::get('threads/{id}', [ForumController::class, 'showThread']);
    Route::put('threads/{id}', [ForumController::class, 'updateThread']);
    Route::delete('threads/{id}', [ForumController::class, 'deleteThread']);
    Route::post('threads/{id}/pin', [ForumController::class, 'togglePin']);
    Route::post('threads/{id}/lock', [ForumController::class, 'toggleLock']);

    // Posts
    Route::get('threads/{threadId}/posts', [ForumController::class, 'threadPosts']);
    Route::post('posts', [ForumController::class, 'storePost']);
    Route::put('posts/{id}', [ForumController::class, 'updatePost']);
    Route::delete('posts/{id}', [ForumController::class, 'deletePost']);
    Route::post('posts/{id}/mark-solution', [ForumController::class, 'markSolution']);

    // Articles (Blog)
    Route::get('articles', [ForumController::class, 'articles']);
    Route::post('articles', [ForumController::class, 'storeArticle']);
    Route::get('articles/{slug}', [ForumController::class, 'showArticle']);
    Route::put('articles/{slug}', [ForumController::class, 'updateArticle']);
    Route::delete('articles/{slug}', [ForumController::class, 'deleteArticle']);

    // Tags
    Route::get('tags', [ForumController::class, 'tags']);
    Route::post('tags', [ForumController::class, 'storeTag']);

    // Likes
    Route::post('likes', [ForumController::class, 'toggleLike']);

    // Bookmarks
    Route::post('bookmarks', [ForumController::class, 'toggleBookmark']);
    Route::get('bookmarks', [ForumController::class, 'myBookmarks']);
});
