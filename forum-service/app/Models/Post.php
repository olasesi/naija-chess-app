<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\SoftDeletes;

class Post extends Model
{
    use HasUuids, SoftDeletes;

    protected $fillable = ['thread_id', 'author_id', 'body', 'is_solution'];

    protected $casts = ['is_solution' => 'boolean'];

    public function thread()
    {
        return $this->belongsTo(Thread::class);
    }

    public function author()
    {
        return $this->belongsTo(User::class, 'author_id');
    }

    public function likes()
    {
        return $this->morphMany(Like::class, 'likeable');
    }
}
