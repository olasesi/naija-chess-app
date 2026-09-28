<?php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\Thread;
use App\Models\Post;
use App\Models\Article;
use App\Models\Tag;
use App\Models\Like;
use App\Models\Bookmark;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class ForumController extends Controller
{
    // ─── Categories ─────────────────────────────────────────────────────

    public function categories()
    {
        $categories = Category::withCount('threads')
            ->where('is_active', true)
            ->orderBy('display_order')
            ->orderBy('name')
            ->get();
        return $this->success($categories);
    }

    public function storeCategory(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:100',
            'description' => 'nullable|string|max:500',
            'icon' => 'nullable|string|max:50',
            'display_order' => 'integer|min:0',
        ]);
        $category = Category::create($data);
        return $this->success($category, 201);
    }

    // ─── Threads ────────────────────────────────────────────────────────

    public function threads(Request $request)
    {
        $query = Thread::with('category:id,name,slug')
            ->withCount('posts', 'likes');

        if ($request->filled('category_id')) {
            $query->where('category_id', $request->category_id);
        }

        if ($request->filled('search')) {
            $search = $request->search;
            $query->where(function ($q) use ($search) {
                $q->where('title', 'like', "%{$search}%")
                  ->orWhere('body', 'like', "%{$search}%");
            });
        }

        if ($request->filled('author_id')) {
            $query->where('author_id', $request->author_id);
        }

        $query->orderBy('is_pinned', 'desc')
            ->orderBy('last_post_at', 'desc')
            ->orderBy('created_at', 'desc');

        $threads = $query->paginate($request->per_page ?? 20);
        return $this->success($threads);
    }

    public function showThread(string $id)
    {
        $thread = Thread::with('category:id,name,slug')
            ->withCount('posts', 'likes')
            ->findOrFail($id);
        return $this->success($thread);
    }

    public function storeThread(Request $request)
    {
        $data = $request->validate([
            'category_id' => 'required|exists:categories,id',
            'title' => 'required|string|max:255',
            'body' => 'required|string',
            'tags' => 'nullable|array',
            'tags.*' => 'exists:tags,id',
        ]);

        $data['author_id'] = $request->x_user_id;

        $thread = DB::transaction(function () use ($data) {
            $thread = Thread::create($data);
            if (!empty($data['tags'])) {
                $thread->tags()->attach($data['tags']);
            }
            return $thread;
        });

        $thread->load('category:id,name,slug');
        return $this->success($thread, 201);
    }

    public function updateThread(Request $request, string $id)
    {
        $thread = Thread::findOrFail($id);

        if ($thread->author_id !== $request->x_user_id) {
            return $this->error('Forbidden', 403);
        }

        $data = $request->validate([
            'title' => 'sometimes|string|max:255',
            'body' => 'sometimes|string',
            'category_id' => 'sometimes|exists:categories,id',
        ]);

        $thread->update($data);
        return $this->success($thread);
    }

    public function deleteThread(string $id)
    {
        $thread = Thread::findOrFail($id);
        $thread->delete();
        return $this->success(null, 200, 'Thread deleted');
    }

    public function togglePin(string $id)
    {
        $thread = Thread::findOrFail($id);
        $thread->update(['is_pinned' => !$thread->is_pinned]);
        return $this->success($thread);
    }

    public function toggleLock(string $id)
    {
        $thread = Thread::findOrFail($id);
        $thread->update(['is_locked' => !$thread->is_locked]);
        return $this->success($thread);
    }

    // ─── Posts ──────────────────────────────────────────────────────────

    public function threadPosts(Request $request, string $threadId)
    {
        $posts = Post::where('thread_id', $threadId)
            ->withCount('likes')
            ->orderBy('created_at')
            ->paginate($request->per_page ?? 20);
        return $this->success($posts);
    }

    public function storePost(Request $request)
    {
        $data = $request->validate([
            'thread_id' => 'required|exists:threads,id',
            'body' => 'required|string',
        ]);

        $thread = Thread::findOrFail($data['thread_id']);
        if ($thread->is_locked) {
            return $this->error('Thread is locked', 423);
        }

        $post = Post::create([
            'thread_id' => $data['thread_id'],
            'author_id' => $request->x_user_id,
            'body' => $data['body'],
        ]);

        $thread->update(['last_post_at' => now()]);

        return $this->success($post->loadCount('likes'), 201);
    }

    public function updatePost(Request $request, string $id)
    {
        $post = Post::findOrFail($id);

        if ($post->author_id !== $request->x_user_id) {
            return $this->error('Forbidden', 403);
        }

        $data = $request->validate(['body' => 'required|string']);
        $post->update($data);
        return $this->success($post);
    }

    public function deletePost(string $id)
    {
        $post = Post::findOrFail($id);
        $post->delete();
        return $this->success(null, 200, 'Post deleted');
    }

    public function markSolution(string $id)
    {
        $post = Post::with('thread')->findOrFail($id);
        $post->update(['is_solution' => !$post->is_solution]);
        return $this->success($post);
    }

    // ─── Articles (Blog) ────────────────────────────────────────────────

    public function articles(Request $request)
    {
        $query = Article::with('tags:id,name,slug')
            ->withCount('likes');

        if (!$request->filled('all') || $request->all !== '1') {
            $query->published();
        }

        if ($request->filled('tag')) {
            $query->whereHas('tags', fn($q) => $q->where('slug', $request->tag));
        }

        if ($request->filled('search')) {
            $search = $request->search;
            $query->where(function ($q) use ($search) {
                $q->where('title', 'like', "%{$search}%")
                  ->orWhere('body', 'like', "%{$search}%");
            });
        }

        $query->orderBy('published_at', 'desc')->orderBy('created_at', 'desc');
        $articles = $query->paginate($request->per_page ?? 10);
        return $this->success($articles);
    }

    public function showArticle(string $slug)
    {
        $article = Article::with('tags:id,name,slug')
            ->withCount('likes')
            ->where('slug', $slug)
            ->firstOrFail();
        return $this->success($article);
    }

    public function storeArticle(Request $request)
    {
        $data = $request->validate([
            'title' => 'required|string|max:255',
            'body' => 'required|string',
            'excerpt' => 'nullable|string|max:500',
            'featured_image' => 'nullable|url|max:2048',
            'is_published' => 'boolean',
            'tags' => 'nullable|array',
            'tags.*' => 'exists:tags,id',
        ]);

        $data['author_id'] = $request->x_user_id;
        if (!empty($data['is_published']) && empty($data['published_at'])) {
            $data['published_at'] = now();
        }

        $article = DB::transaction(function () use ($data) {
            $article = Article::create($data);
            if (!empty($data['tags'])) {
                $article->tags()->attach($data['tags']);
            }
            return $article;
        });

        $article->load('tags:id,name,slug');
        return $this->success($article, 201);
    }

    public function updateArticle(Request $request, string $slug)
    {
        $article = Article::where('slug', $slug)->firstOrFail();

        $data = $request->validate([
            'title' => 'sometimes|string|max:255',
            'body' => 'sometimes|string',
            'excerpt' => 'nullable|string|max:500',
            'featured_image' => 'nullable|url|max:2048',
            'is_published' => 'boolean',
            'tags' => 'nullable|array',
            'tags.*' => 'exists:tags,id',
        ]);

        if (!empty($data['is_published']) && empty($article->published_at)) {
            $data['published_at'] = now();
        }

        DB::transaction(function () use ($article, $data) {
            $article->update($data);
            if (isset($data['tags'])) {
                $article->tags()->sync($data['tags']);
            }
        });

        $article->load('tags:id,name,slug');
        return $this->success($article);
    }

    public function deleteArticle(string $slug)
    {
        $article = Article::where('slug', $slug)->firstOrFail();
        $article->delete();
        return $this->success(null, 200, 'Article deleted');
    }

    // ─── Tags ───────────────────────────────────────────────────────────

    public function tags()
    {
        $tags = Tag::orderBy('name')->get();
        return $this->success($tags);
    }

    public function storeTag(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:50|unique:tags,name',
        ]);
        $tag = Tag::create($data);
        return $this->success($tag, 201);
    }

    // ─── Likes ──────────────────────────────────────────────────────────

    public function toggleLike(Request $request)
    {
        $data = $request->validate([
            'likeable_type' => 'required|in:thread,post,article',
            'likeable_id' => 'required|string',
        ]);

        $typeMap = [
            'thread' => Thread::class,
            'post' => Post::class,
            'article' => Article::class,
        ];

        $type = $typeMap[$data['likeable_type']];
        $like = Like::where('user_id', $request->x_user_id)
            ->where('likeable_type', $type)
            ->where('likeable_id', $data['likeable_id'])
            ->first();

        if ($like) {
            $like->delete();
            return $this->success(['liked' => false]);
        }

        Like::create([
            'user_id' => $request->x_user_id,
            'likeable_type' => $type,
            'likeable_id' => $data['likeable_id'],
        ]);
        return $this->success(['liked' => true]);
    }

    // ─── Bookmarks ─────────────────────────────────────────────────────

    public function toggleBookmark(Request $request)
    {
        $data = $request->validate([
            'bookmarkable_type' => 'required|in:thread,article',
            'bookmarkable_id' => 'required|string',
        ]);

        $typeMap = [
            'thread' => Thread::class,
            'article' => Article::class,
        ];

        $type = $typeMap[$data['bookmarkable_type']];
        $bookmark = Bookmark::where('user_id', $request->x_user_id)
            ->where('bookmarkable_type', $type)
            ->where('bookmarkable_id', $data['bookmarkable_id'])
            ->first();

        if ($bookmark) {
            $bookmark->delete();
            return $this->success(['bookmarked' => false]);
        }

        Bookmark::create([
            'user_id' => $request->x_user_id,
            'bookmarkable_type' => $type,
            'bookmarkable_id' => $data['bookmarkable_id'],
        ]);
        return $this->success(['bookmarked' => true]);
    }

    public function myBookmarks(Request $request)
    {
        $data = $request->validate(['type' => 'nullable|in:thread,article']);
        $type = $data['type'] ?? 'thread';
        $typeMap = ['thread' => Thread::class, 'article' => Article::class];
        $class = $typeMap[$type] ?? Thread::class;

        $bookmarks = Bookmark::where('user_id', $request->x_user_id)
            ->where('bookmarkable_type', $class)
            ->with('bookmarkable')
            ->orderBy('created_at', 'desc')
            ->paginate($request->per_page ?? 20);
        return $this->success($bookmarks);
    }

    // ─── Helpers ────────────────────────────────────────────────────────

    private function success($data, int $status = 200, string $message = 'Success')
    {
        if ($data instanceof \Illuminate\Contracts\Pagination\LengthAwarePaginator) {
            return response()->json([
                'success' => true,
                'message' => $message,
                'data' => $data->items(),
                'meta' => [
                    'current_page' => $data->currentPage(),
                    'last_page' => $data->lastPage(),
                    'per_page' => $data->perPage(),
                    'total' => $data->total(),
                ],
            ], $status);
        }
        return response()->json(['success' => true, 'message' => $message, 'data' => $data], $status);
    }

    private function error(string $message, int $status = 400)
    {
        return response()->json(['success' => false, 'message' => $message], $status);
    }
}
