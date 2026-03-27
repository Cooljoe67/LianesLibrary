use sys;

drop database if exists LianesLibrary;

create database LianesLibrary
    default character set utf8mb4
    default collate utf8mb4_unicode_ci;

use LianesLibrary;
-- drop user if exists 'Liane'@'localhost';
-- create user 'Liane'@'localhost' identified by 'LibPass2025!';
-- grant select, insert, update on LibraryDB.* to 'library_user'@'localhost';
-- flush privileges;

create table books (
    book_id int auto_increment primary key
    , isbn varchar(20) not null
    , title varchar(255) not null
    , author varchar(255)
    , cpy int DEFAULT 1 
);

create table readers (
    reader_id int auto_increment primary key
    , last_name varchar(255) not null
    , first_name varchar(255) not null
    , email varchar(255) 
    , phone varchar(50)
);

create table checkouts (
    checkout_id int auto_increment primary key
	, book_id int not null
    , reader_id int not null
    , loan_date date not null
    , due_date date null
    , return_date date null
);


