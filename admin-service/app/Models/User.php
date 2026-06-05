<?php
namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;

class User extends Authenticatable
{
    protected $fillable = ['id', 'email', 'username', 'role'];
    public $incrementing = false;
    protected $keyType = 'string';
}
