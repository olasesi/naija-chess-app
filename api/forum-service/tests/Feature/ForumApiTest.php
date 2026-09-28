<?php
namespace Tests\Feature;

use App\Models\Category;
use App\Models\Thread;
use App\Models\Post;
use App\Models\Article;
use App\Models\Tag;
use App\Models\Like;
use App\Models\Bookmark;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Tests\TestCase;

class ForumApiTest extends TestCase
{
    use RefreshDatabase;

    protected function authHeaders(string $userId = 'user-1', string $email = 'test@test.com', string $role = 'PLAYER'): array
    {
        return [
            'X-User-Id' => $userId,
            'X-User-Email' => $email,
            'X-User-Role' => $role,
            'Accept' => 'application/json',
        ];
    }

    public function test_categories_list()
    {
        Category::create(['name' => 'General', 'display_order' => 1]);
        Category::create(['name' => 'Tournaments', 'display_order' => 2]);

        $response = $this->getJson('/api/forum/categories', $this->authHeaders());
        $response->assertStatus(200)
            ->assertJson(['success' => true])
            ->assertJsonCount(2, 'data');
    }

    public function test_create_category()
    {
        $response = $this->postJson('/api/forum/categories', [
            'name' => 'New Category',
            'description' => 'Test',
        ], $this->authHeaders());

        $response->assertStatus(201)
            ->assertJsonPath('data.name', 'New Category');
    }

    public function test_create_thread()
    {
        $category = Category::create(['name' => 'General']);

        $response = $this->postJson('/api/forum/threads', [
            'category_id' => $category->id,
            'title' => 'Hello World',
            'body' => 'This is a test thread',
        ], $this->authHeaders());

        $response->assertStatus(201)
            ->assertJson(['success' => true])
            ->assertJsonPath('data.title', 'Hello World')
            ->assertJsonPath('data.author_id', 'user-1');
    }

    public function test_list_threads()
    {
        $cat = Category::create(['name' => 'General']);
        Thread::create(['category_id' => $cat->id, 'title' => 'T1', 'body' => 'B1', 'author_id' => 'u1']);
        Thread::create(['category_id' => $cat->id, 'title' => 'T2', 'body' => 'B2', 'author_id' => 'u2']);

        $response = $this->getJson('/api/forum/threads', $this->authHeaders());
        $response->assertStatus(200)
            ->assertJsonPath('meta.total', 2);
    }

    public function test_show_thread()
    {
        $cat = Category::create(['name' => 'General']);
        $thread = Thread::create(['category_id' => $cat->id, 'title' => 'Test', 'body' => 'Body', 'author_id' => 'u1']);

        $response = $this->getJson("/api/forum/threads/{$thread->id}", $this->authHeaders());
        $response->assertStatus(200)
            ->assertJsonPath('data.title', 'Test');
    }

    public function test_create_post()
    {
        $cat = Category::create(['name' => 'General']);
        $thread = Thread::create(['category_id' => $cat->id, 'title' => 'Test', 'body' => 'Body', 'author_id' => 'u1']);

        $response = $this->postJson('/api/forum/posts', [
            'thread_id' => $thread->id,
            'body' => 'Nice thread!',
        ], $this->authHeaders('user-2'));

        $response->assertStatus(201)
            ->assertJsonPath('data.body', 'Nice thread!');
    }

    public function test_cannot_post_to_locked_thread()
    {
        $cat = Category::create(['name' => 'General']);
        $thread = Thread::create([
            'category_id' => $cat->id, 'title' => 'Test', 'body' => 'Body',
            'author_id' => 'u1', 'is_locked' => true,
        ]);

        $response = $this->postJson('/api/forum/posts', [
            'thread_id' => $thread->id,
            'body' => 'Nope',
        ], $this->authHeaders('user-2'));

        $response->assertStatus(423);
    }

    public function test_list_articles()
    {
        Article::create([
            'title' => 'Published Article', 'body' => 'Content',
            'author_id' => 'u1', 'is_published' => true, 'published_at' => now(),
        ]);
        Article::create([
            'title' => 'Draft', 'body' => 'Draft content',
            'author_id' => 'u1', 'is_published' => false,
        ]);

        $response = $this->getJson('/api/forum/articles', $this->authHeaders());
        $response->assertStatus(200)
            ->assertJsonPath('meta.total', 1);
    }

    public function test_create_article()
    {
        $response = $this->postJson('/api/forum/articles', [
            'title' => 'Chess Strategy',
            'body' => 'Some strategy content',
            'excerpt' => 'A short excerpt',
            'is_published' => true,
        ], $this->authHeaders('admin-1'));

        $response->assertStatus(201)
            ->assertJsonPath('data.title', 'Chess Strategy');
    }

    public function test_toggle_like()
    {
        $cat = Category::create(['name' => 'General']);
        $thread = Thread::create(['category_id' => $cat->id, 'title' => 'Test', 'body' => 'Body', 'author_id' => 'u1']);

        $response = $this->postJson('/api/forum/likes', [
            'likeable_type' => 'thread',
            'likeable_id' => $thread->id,
        ], $this->authHeaders('user-2'));

        $response->assertStatus(200)
            ->assertJsonPath('data.liked', true);

        $response = $this->postJson('/api/forum/likes', [
            'likeable_type' => 'thread',
            'likeable_id' => $thread->id,
        ], $this->authHeaders('user-2'));

        $response->assertStatus(200)
            ->assertJsonPath('data.liked', false);
    }

    public function test_requires_auth()
    {
        $response = $this->getJson('/api/forum/threads');
        $response->assertStatus(401);
    }

    public function test_tags()
    {
        Tag::create(['name' => 'Opening']);
        Tag::create(['name' => 'Endgame']);

        $response = $this->getJson('/api/forum/tags', $this->authHeaders());
        $response->assertStatus(200)
            ->assertJsonCount(2, 'data');
    }

    public function test_bookmark_toggle()
    {
        $cat = Category::create(['name' => 'General']);
        $thread = Thread::create(['category_id' => $cat->id, 'title' => 'Test', 'body' => 'Body', 'author_id' => 'u1']);

        $response = $this->postJson('/api/forum/bookmarks', [
            'bookmarkable_type' => 'thread',
            'bookmarkable_id' => $thread->id,
        ], $this->authHeaders('user-1'));

        $response->assertStatus(200)
            ->assertJsonPath('data.bookmarked', true);
    }

    public function test_mark_solution()
    {
        $cat = Category::create(['name' => 'General']);
        $thread = Thread::create(['category_id' => $cat->id, 'title' => 'Q', 'body' => 'Help', 'author_id' => 'u1']);
        $post = Post::create(['thread_id' => $thread->id, 'author_id' => 'u2', 'body' => 'Answer']);

        $response = $this->postJson("/api/forum/posts/{$post->id}/mark-solution", [], $this->authHeaders());
        $response->assertStatus(200)
            ->assertJsonPath('data.is_solution', true);
    }
}
