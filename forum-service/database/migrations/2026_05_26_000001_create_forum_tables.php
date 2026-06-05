<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('categories', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('name');
            $table->string('slug')->unique();
            $table->text('description')->nullable();
            $table->string('icon')->nullable();
            $table->integer('display_order')->default(0);
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('threads', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('category_id')->constrained()->cascadeOnDelete();
            $table->string('title');
            $table->string('slug')->unique();
            $table->longText('body');
            $table->string('author_id');
            $table->boolean('is_pinned')->default(false);
            $table->boolean('is_locked')->default(false);
            $table->timestamp('last_post_at')->nullable();
            $table->softDeletes();
            $table->timestamps();
            $table->index(['category_id', 'is_pinned', 'deleted_at']);
            $table->index(['author_id']);
        });

        Schema::create('posts', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('thread_id')->constrained()->cascadeOnDelete();
            $table->string('author_id');
            $table->longText('body');
            $table->boolean('is_solution')->default(false);
            $table->softDeletes();
            $table->timestamps();
            $table->index(['thread_id', 'deleted_at']);
            $table->index(['author_id']);
        });

        Schema::create('articles', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('title');
            $table->string('slug')->unique();
            $table->longText('body');
            $table->text('excerpt')->nullable();
            $table->string('author_id');
            $table->string('featured_image')->nullable();
            $table->boolean('is_published')->default(false);
            $table->timestamp('published_at')->nullable();
            $table->softDeletes();
            $table->timestamps();
            $table->index(['is_published', 'published_at', 'deleted_at']);
        });

        Schema::create('tags', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('name');
            $table->string('slug')->unique();
            $table->timestamps();
        });

        Schema::create('taggables', function (Blueprint $table) {
            $table->foreignUuid('tag_id')->constrained()->cascadeOnDelete();
            $table->morphs('taggable');
            $table->unique(['tag_id', 'taggable_id', 'taggable_type']);
        });

        Schema::create('likes', function (Blueprint $table) {
            $table->id();
            $table->string('user_id');
            $table->morphs('likeable');
            $table->timestamps();
            $table->unique(['user_id', 'likeable_id', 'likeable_type']);
        });

        Schema::create('bookmarks', function (Blueprint $table) {
            $table->id();
            $table->string('user_id');
            $table->morphs('bookmarkable');
            $table->timestamps();
            $table->unique(['user_id', 'bookmarkable_id', 'bookmarkable_type']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('bookmarks');
        Schema::dropIfExists('likes');
        Schema::dropIfExists('taggables');
        Schema::dropIfExists('tags');
        Schema::dropIfExists('articles');
        Schema::dropIfExists('posts');
        Schema::dropIfExists('threads');
        Schema::dropIfExists('categories');
    }
};
