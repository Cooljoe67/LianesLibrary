drop view if exists v_readers;
create view v_readers as 
select 
	first_name as 'first name', 
	last_name as 'fast name',
    email, 
    phone, 
    case (select count(*) from checkouts c where c.reader_id = r.reader_id) when 0 then '*NO*' else '*YES*' end as 'has books',
    (select count(*) from checkouts c where c.reader_id = r.reader_id) as 'no of books'
from readers r;

drop view if exists v_books;

create view v_books as 
select concat(isbn, case when cpy >1 then concat(' (', cpy,')') else '' end) as 'ISBN (copy)'
	, Title
    , Author
    , case when checkout_id is null then '*HERE*' else '*GONE*' end as 'Here?'
    , concat(first_name, ' ', last_name) as 'Curr. Reader'
from books b
left join (select * from checkouts c where return_date is null) c using (book_id)
left join readers r using (reader_id);


drop view if exists v_checkouts;
create view v_checkouts as 
select Title, Author, concat (first_name, ' ', last_name) as Reader, 
	case when return_date is null then '*GONE*' else '*BACK*' end as 'Back?', 
	case when current_date() > due_date and return_date is null then '💀' else '' end as 'Overdue?', 
    Loan_date as 'Loan Date', Due_date as 'Due Date', 
    return_date as 'Return Date'
from checkouts
join readers using (reader_id)
join books using (book_id);


select * from v_books;
select * from v_readers;

select * from checkouts;


delete from books where book_id=92;
delete from checkouts where book_id in (80,96);

select * from books where isbn='9780000001080';
select * from checkouts where book_id in (80,96);

drop view if exists search_readers;

DELIMITER $$

CREATE PROCEDURE filter_view(
    IN p_table VARCHAR(128),
    IN p_search TEXT
)
BEGIN
    DECLARE v_sql LONGTEXT;
    DECLARE v_word TEXT;
    DECLARE v_pos INT;
    DECLARE v_cols TEXT;

    -- Build base query
    SET v_sql = CONCAT('SELECT * FROM `', p_table, '` WHERE 1=1');

    -- Fetch all column names dynamically
    SELECT GROUP_CONCAT(CONCAT('`', COLUMN_NAME, '`') SEPARATOR ',')
    INTO v_cols
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table;

    -- Normalize input
    SET p_search = TRIM(p_search);

    -- Loop through each word
    WHILE p_search <> '' DO

        -- Extract next word
        SET v_pos = LOCATE(' ', p_search);
        IF v_pos = 0 THEN
            SET v_word = p_search;
            SET p_search = '';
        ELSE
            SET v_word = SUBSTRING(p_search, 1, v_pos - 1);
            SET p_search = SUBSTRING(p_search, v_pos + 1);
        END IF;

        SET v_word = TRIM(v_word);

        -- Quoted → exact match
        IF (LEFT(v_word,1) = '"' AND RIGHT(v_word,1) = '"')
           OR (LEFT(v_word,1) = '\'' AND RIGHT(v_word,1) = '\'') THEN

            SET v_word = SUBSTRING(v_word, 2, CHAR_LENGTH(v_word)-2);

            SET v_sql = CONCAT(
                v_sql,
                ' AND (',
                REPLACE(v_cols, ',', CONCAT(" = '", v_word, "' OR ")),
                " = '", v_word, "')"
            );

        ELSE
            -- LIKE match
            SET v_sql = CONCAT(
                v_sql,
                ' AND (',
                REPLACE(v_cols, ',', CONCAT(" LIKE '%", v_word, "%' OR ")),
                " LIKE '%", v_word, "%')"
            );
        END IF;

    END WHILE;

    -- Dynamic SQL requires a session variable
    SET @sql = v_sql;

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

END$$

DELIMITER ;
call filter_view('v_books', '*GONE* jane');