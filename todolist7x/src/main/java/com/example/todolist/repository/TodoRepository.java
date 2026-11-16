package com.example.todolist.repository;

import java.time.LocalDate;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.example.todolist.entity.Todo;

@Repository
public interface TodoRepository extends JpaRepository<Todo, Integer> {
    List<Todo> findByTitleLike(String title);

    List<Todo> findByImportance(Integer importance);

    List<Todo> findByUrgency(Integer urgency);

    List<Todo> findByDeadlineBetweenOrderByDeadlineAsc(LocalDate from, LocalDate to);

    List<Todo> findByDeadlineGreaterThanEqualOrderByDeadlineAsc(LocalDate from);

    List<Todo> findByDeadlineLessThanEqualOrderByDeadlineAsc(LocalDate to);

    List<Todo> findByDone(String done);

    // @formatter:off
    static final String WHERE_CLAUSE = """
            WHERE (CAST(:title AS text) IS NULL OR title LIKE :title)
              AND (CAST(:importance AS integer) IS NULL OR importance = :importance)
              AND (CAST(:urgency AS integer)    IS NULL OR urgency    = :urgency)
              AND (CAST(:deadlineFrom AS date)  IS NULL OR deadline  >= :deadlineFrom )
              AND (CAST(:deadlineTo   AS date)  IS NULL OR deadline  <= :deadlineTo)
              AND (CAST(:done AS text) IS NULL OR done = :done)
             """;

    @Query(value = "SELECT * FROM todo " + WHERE_CLAUSE + "ORDER BY id", 
            countQuery = "SELECT COUNT(*) FROM todo " + WHERE_CLAUSE, 
            nativeQuery = true)
    Page<Todo> searchByNativeQuery(
            @Param("title") String title,
            @Param("importance") Integer importance,
            @Param("urgency") Integer urgency,
            @Param("deadlineFrom") LocalDate deadlineFrom,
            @Param("deadlineTo") LocalDate deadlineTo,
            @Param("done") String done,
            Pageable pageable);
    // @formatter:on
}