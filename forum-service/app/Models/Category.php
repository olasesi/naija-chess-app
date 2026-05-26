<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Spatie\Sluggable\HasSlug;
use Spatie\Sluggable\SlugOptions;

class Category extends Model
{
    use HasUuids, HasSlug;

    protected $fillable = ['name', 'description', 'icon', 'display_order', 'is_active'];

    protected $casts = ['is_active' => 'boolean'];

    public function getSlugOptions(): SlugOptions
    {
        return SlugOptions::create()
            ->generateSlugsFrom('name')
            ->saveSlugsTo('slug');
    }

    public function threads()
    {
        return $this->hasMany(Thread::class);
    }
}
