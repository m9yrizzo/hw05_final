from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .models import Post, Group, Follow
from .forms import PostForm, CommentForm


User = get_user_model()


POST_PER_PAGE = settings.POST_PER_PAGE


def paginatorer(request, query_set):
    paginator = Paginator(query_set, POST_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    posts = (
        Post.objects.select_related('author', 'group')
    )
    page_obj = paginatorer(request, posts)
    return render(request, 'posts/index.html', {'page_obj': page_obj, })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = (
        group.posts.select_related('author')
    )
    page_obj = paginatorer(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginatorer(request, posts)
    return render(request, 'posts/follow.html', {'page_obj': page_obj, })


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    following_author = get_object_or_404(User, username=username)
    if (request.user != following_author):
        Follow.objects.get_or_create(
            user=request.user,
            author=following_author,
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    following_author = get_object_or_404(User, username=username)
    if (request.user != following_author):
        Follow.objects.filter(
            user=request.user,
            author=following_author
        ).delete()
    return redirect('posts:profile', username=username)


def profile(request, username):
    following_author = get_object_or_404(User, username=username)
    posts = (
        following_author.posts.select_related('author', 'group')
    )
    page_obj = paginatorer(request, posts)
    if (request.user.is_authenticated and request.user != following_author):
        following = Follow.objects.filter(
            user=request.user, author=following_author
        ).exists()
        button_visible = True
    else:
        following = False
        button_visible = False
    context = {
        'page_obj': page_obj,
        'author': following_author,
        'following': following,
        'button_visible': button_visible
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    can_edit = request.user == post.author
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'can_edit': can_edit,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    is_edit = False
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.pub_date = datetime.now()
        post.save()
        return redirect('posts:profile', username=post.author.username)
    return render(
        request, 'posts/post_create.html',
        {'form': form, 'is_edit': is_edit, }
    )


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if (request.user == post.author):
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.pub_date = datetime.now()
            post.save()
            return redirect('posts:post_detail', post_id=post_id)
        return render(
            request, 'posts/post_create.html',
            {'form': form, 'is_edit': is_edit, }
        )
    else:
        return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect("posts:post_detail", post_id=post_id)
