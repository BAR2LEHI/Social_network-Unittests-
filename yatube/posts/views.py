from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import paginate_page

NUM_POST: int = 10

User = get_user_model()


def index(request):
    """Функция отображения главной страницы"""
    posts_list = Post.objects.all()
    context = {
        'page_obj': paginate_page(request, posts_list)
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Функция отображения постов группы"""
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    context = {
        'page_obj': paginate_page(request, posts_list),
        'group': group
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Функция отображения профиля пользователя"""
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.all()
    user = request.user
    following = Follow.objects.filter(user=user, author=author).exists()
    context = {
        'page_obj': paginate_page(request, posts_list),
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Функция детального отображения поста"""
    one_post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = one_post.comments.all()
    context = {
        'one_post': one_post,
        'form': form,
        'comments': comments,
        'post_id': post_id
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Функция создания нового поста"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Функция редактирования поста"""
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.author = request.user
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'is_edit': True,
        'form': form,
        'post_id': post_id
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.create(
        user=request.user,
        author=author
    )
    return redirect('posts:profile', username)


@login_required
def follow_index(request):
    user = request.user
    authors = user.follower.values_list('author', flat=True)
    post_list = Post.objects.filter(author__id__in=authors)
    context = {
        'page_obj': paginate_page(request, post_list)
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
